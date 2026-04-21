import json
import time
import urllib.error
import urllib.parse
import urllib.request

from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require


class ElementCall(IntervalModule):
    """
    Displays the number of active participants in an Element Call room on a
    Matrix homeserver. Uses the Matrix Client-Server API to read
    ``org.matrix.msc3401.call.member`` state events and counts members whose
    session has not yet expired.

    Requires a Matrix access token with read access to the target room.

    .. rubric:: Available formatters

    * ``{participants}`` — number of active call participants
    * ``{room_id}`` — the Matrix room ID being monitored
    * ``{room_alias}`` — the room_alias setting value

    .. rubric:: Example configuration

    .. code-block:: python

        status.register(
            "element_call",
            homeserver="https://matrix.example.com",
            access_token="syt_...",
            room_id="!abc123:example.com",
            format_active="\U0001F4DE {participants}",
            format_empty="\U0001F4DE",
            interval=15,
        )
    """

    settings = (
        ("homeserver", "Base URL of your Matrix homeserver (e.g. https://matrix.example.com)"),
        ("access_token", "Matrix access token with read access to the room"),
        ("room_id", "Matrix room ID to monitor (e.g. !abc123:example.com)"),
        ("room_alias", "Human-readable label used in {room_alias} formatter"),
        ("format_active", "Format string when participants > 0"),
        ("format_empty", "Format string when no one is in the call"),
        ("format_error", "Format string on API error"),
        ("color_active", "Color when participants > 0"),
        ("color_empty", "Color when call is empty"),
        ("color_error", "Color on API error"),
        ("interval", "Polling interval in seconds"),
    )

    homeserver = ""
    access_token = ""
    room_id = ""
    room_alias = ""
    format_active = "\U0001F4DE {participants}"
    format_empty = ""
    format_error = "\U0001F4DE ?"
    color_active = "#00FF00"
    color_empty = "#888888"
    color_error = "#FF0000"
    interval = 15

    # MSC3401 state event type used by Element Call
    _CALL_MEMBER_TYPE = "org.matrix.msc3401.call.member"

    @require(internet)
    def run(self):
        try:
            participants = self._count_participants()
        except Exception:
            self.output = {
                "full_text": self.format_error,
                "color": self.color_error,
            }
            return

        fdict = {
            "participants": participants,
            "room_id": self.room_id,
            "room_alias": self.room_alias,
        }

        if participants > 0:
            self.output = {
                "full_text": self.format_active.format(**fdict),
                "color": self.color_active,
            }
        else:
            self.output = {
                "full_text": self.format_empty.format(**fdict),
                "color": self.color_empty,
            }

    def _resolve_room_id(self, room_id_or_alias):
        """Resolve a room alias (#name:server) to a room ID (!id:server) if needed."""
        if room_id_or_alias.startswith("!"):
            return room_id_or_alias
        url = "{homeserver}/_matrix/client/v3/directory/room/{alias}".format(
            homeserver=self.homeserver.rstrip("/"),
            alias=urllib.parse.quote(room_id_or_alias, safe=""),
        )
        req = urllib.request.Request(
            url,
            headers={"Authorization": "Bearer {}".format(self.access_token)},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["room_id"]

    def _count_participants(self):
        """Return the number of active call participants in the room."""
        resolved_id = self._resolve_room_id(self.room_id)
        url = "{homeserver}/_matrix/client/v3/rooms/{room_id}/state".format(
            homeserver=self.homeserver.rstrip("/"),
            room_id=urllib.parse.quote(resolved_id, safe=""),
        )
        req = urllib.request.Request(
            url,
            headers={"Authorization": "Bearer {}".format(self.access_token)},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            state_events = json.loads(resp.read().decode("utf-8"))

        now_ms = int(time.time() * 1000)
        active_users = set()

        for event in state_events:
            if event.get("type") != self._CALL_MEMBER_TYPE:
                continue

            content = event.get("content", {})
            if not content:
                # Empty content means the member has left
                continue

            user_id = event.get("sender") or event.get("user_id", "")
            state_key = event.get("state_key", "")

            origin_ts = event.get("origin_server_ts", 0)

            if state_key.startswith("@"):
                # Per-user format: content has a "memberships" list
                for membership in content.get("memberships", []):
                    if self._membership_active(membership, now_ms, origin_ts):
                        active_users.add(user_id)
                        break
            else:
                # Per-device format: content itself is the membership object
                if self._membership_active(content, now_ms, origin_ts):
                    active_users.add(user_id)

        return len(active_users)

    def _membership_active(self, membership, now_ms, origin_ts=0):
        """Return True if this membership entry has not yet expired."""
        expires = membership.get("expires", 0)
        if not expires:
            return False
        # Values > 1e12 are absolute epoch-ms timestamps.
        # Smaller values are relative durations; anchor to created_ts, falling
        # back to origin_server_ts from the event if created_ts is absent.
        if expires > 1_000_000_000_000:
            return expires > now_ms
        created_ts = membership.get("created_ts") or origin_ts
        return (created_ts + expires) > now_ms
