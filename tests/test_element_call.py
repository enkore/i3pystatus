import io
import json
import unittest
from unittest.mock import MagicMock, call, patch

from i3pystatus.element_call import ElementCall

# Freeze time: 2026-04-21T00:00:00Z in milliseconds
NOW_MS = 1_776_729_600_000

ROOM_ALIAS = "#myroom:example.com"
ROOM_ID = "!abc123:example.com"
HOMESERVER = "https://matrix.example.com"
ACCESS_TOKEN = "syt_test_token"


def make_plugin(**kwargs):
    ec = ElementCall.__new__(ElementCall)
    ec.homeserver = HOMESERVER
    ec.access_token = ACCESS_TOKEN
    ec.room_id = kwargs.get("room_id", ROOM_ID)
    ec.room_alias = kwargs.get("room_alias", "")
    ec.format_active = kwargs.get("format_active", "\U0001F4DE {participants}")
    ec.format_empty = kwargs.get("format_empty", "")
    ec.format_error = kwargs.get("format_error", "\U0001F4DE ?")
    ec.color_active = kwargs.get("color_active", "#00FF00")
    ec.color_empty = kwargs.get("color_empty", "#888888")
    ec.color_error = kwargs.get("color_error", "#FF0000")
    return ec


def urlopen_returning(payload):
    """Return a mock context manager that yields a response with the given payload."""
    body = json.dumps(payload).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def make_call_event(state_key, sender, content, origin_server_ts=NOW_MS):
    return {
        "type": "org.matrix.msc3401.call.member",
        "state_key": state_key,
        "sender": sender,
        "content": content,
        "origin_server_ts": origin_server_ts,
    }


# ---------------------------------------------------------------------------
# _membership_active
# ---------------------------------------------------------------------------

class TestMembershipActive(unittest.TestCase):

    def setUp(self):
        self.ec = make_plugin()

    def test_absolute_timestamp_future(self):
        membership = {"expires": NOW_MS + 60_000}
        self.assertTrue(self.ec._membership_active(membership, NOW_MS))

    def test_absolute_timestamp_past(self):
        membership = {"expires": NOW_MS - 1}
        self.assertFalse(self.ec._membership_active(membership, NOW_MS))

    def test_relative_duration_with_created_ts_active(self):
        # created 1 hour ago, 4-hour duration → still active
        created_ts = NOW_MS - 3_600_000
        membership = {"expires": 14_400_000, "created_ts": created_ts}
        self.assertTrue(self.ec._membership_active(membership, NOW_MS))

    def test_relative_duration_with_created_ts_expired(self):
        # created 5 hours ago, 4-hour duration → expired
        created_ts = NOW_MS - 18_000_000
        membership = {"expires": 14_400_000, "created_ts": created_ts}
        self.assertFalse(self.ec._membership_active(membership, NOW_MS))

    def test_relative_duration_falls_back_to_origin_ts(self):
        # no created_ts; origin_ts is recent enough
        origin_ts = NOW_MS - 3_600_000
        membership = {"expires": 14_400_000}
        self.assertTrue(self.ec._membership_active(membership, NOW_MS, origin_ts))

    def test_relative_duration_origin_ts_expired(self):
        # no created_ts; origin_ts is too old
        origin_ts = NOW_MS - 18_000_000
        membership = {"expires": 14_400_000}
        self.assertFalse(self.ec._membership_active(membership, NOW_MS, origin_ts))

    def test_zero_expires(self):
        self.assertFalse(self.ec._membership_active({"expires": 0}, NOW_MS))

    def test_missing_expires(self):
        self.assertFalse(self.ec._membership_active({}, NOW_MS))


# ---------------------------------------------------------------------------
# _resolve_room_id
# ---------------------------------------------------------------------------

class TestResolveRoomId(unittest.TestCase):

    def setUp(self):
        self.ec = make_plugin()

    def test_room_id_passthrough(self):
        self.assertEqual(self.ec._resolve_room_id(ROOM_ID), ROOM_ID)

    @patch("urllib.request.urlopen")
    def test_alias_resolved(self, mock_urlopen):
        mock_urlopen.return_value = urlopen_returning({"room_id": ROOM_ID, "servers": ["example.com"]})
        result = self.ec._resolve_room_id(ROOM_ALIAS)
        self.assertEqual(result, ROOM_ID)
        url_used = mock_urlopen.call_args[0][0].full_url
        self.assertIn("%23myroom%3Aexample.com", url_used)


# ---------------------------------------------------------------------------
# _count_participants
# ---------------------------------------------------------------------------

class TestCountParticipants(unittest.TestCase):

    def setUp(self):
        self.ec = make_plugin()

    def _run_with_events(self, events):
        with patch("urllib.request.urlopen") as mock_urlopen, \
                patch("time.time", return_value=NOW_MS / 1000):
            mock_urlopen.return_value = urlopen_returning(events)
            return self.ec._count_participants()

    def test_no_events(self):
        self.assertEqual(self._run_with_events([]), 0)

    def test_ignores_non_call_events(self):
        events = [{"type": "m.room.member", "state_key": "@alice:example.com", "content": {"membership": "join"}}]
        self.assertEqual(self._run_with_events(events), 0)

    def test_empty_content_not_counted(self):
        event = make_call_event("_@alice:example.com_DEV1_m.call", "@alice:example.com", {})
        self.assertEqual(self._run_with_events([event]), 0)

    def test_per_device_active(self):
        content = {"expires": 14_400_000}
        event = make_call_event(
            "_@alice:example.com_DEV1_m.call", "@alice:example.com",
            content, origin_server_ts=NOW_MS - 3_600_000,
        )
        self.assertEqual(self._run_with_events([event]), 1)

    def test_per_device_expired(self):
        content = {"expires": 14_400_000}
        event = make_call_event(
            "_@alice:example.com_DEV1_m.call", "@alice:example.com",
            content, origin_server_ts=NOW_MS - 18_000_000,
        )
        self.assertEqual(self._run_with_events([event]), 0)

    def test_per_user_format_active(self):
        content = {"memberships": [{"expires": NOW_MS + 60_000}]}
        event = make_call_event("@alice:example.com", "@alice:example.com", content)
        self.assertEqual(self._run_with_events([event]), 1)

    def test_per_user_format_expired(self):
        content = {"memberships": [{"expires": NOW_MS - 1}]}
        event = make_call_event("@alice:example.com", "@alice:example.com", content)
        self.assertEqual(self._run_with_events([event]), 0)

    def test_two_devices_same_user_counted_once(self):
        content = {"expires": 14_400_000}
        events = [
            make_call_event("_@alice:example.com_DEV1_m.call", "@alice:example.com",
                            content, origin_server_ts=NOW_MS - 3_600_000),
            make_call_event("_@alice:example.com_DEV2_m.call", "@alice:example.com",
                            content, origin_server_ts=NOW_MS - 3_600_000),
        ]
        self.assertEqual(self._run_with_events(events), 1)

    def test_two_users_counted_separately(self):
        content = {"expires": 14_400_000}
        events = [
            make_call_event("_@alice:example.com_DEV1_m.call", "@alice:example.com",
                            content, origin_server_ts=NOW_MS - 3_600_000),
            make_call_event("_@bob:example.com_DEV1_m.call", "@bob:example.com",
                            content, origin_server_ts=NOW_MS - 3_600_000),
        ]
        self.assertEqual(self._run_with_events(events), 2)

    def test_mixed_active_and_left(self):
        active_content = {"expires": 14_400_000}
        events = [
            make_call_event("_@alice:example.com_DEV1_m.call", "@alice:example.com",
                            active_content, origin_server_ts=NOW_MS - 3_600_000),
            make_call_event("_@bob:example.com_DEV1_m.call", "@bob:example.com",
                            {}, origin_server_ts=NOW_MS - 3_600_000),
        ]
        self.assertEqual(self._run_with_events(events), 1)


# ---------------------------------------------------------------------------
# run() — output formatting
# ---------------------------------------------------------------------------

class TestRun(unittest.TestCase):

    def setUp(self):
        self.ec = make_plugin()

    def _run_with_count(self, count):
        with patch.object(self.ec, "_count_participants", return_value=count):
            self.ec.run()

    def test_active_output(self):
        self._run_with_count(2)
        self.assertEqual(self.ec.output["full_text"], "\U0001F4DE 2")
        self.assertEqual(self.ec.output["color"], "#00FF00")

    def test_empty_output(self):
        self._run_with_count(0)
        self.assertEqual(self.ec.output["full_text"], "")
        self.assertEqual(self.ec.output["color"], "#888888")

    def test_error_output(self):
        with patch.object(self.ec, "_count_participants", side_effect=Exception("boom")):
            self.ec.run()
        self.assertEqual(self.ec.output["full_text"], "\U0001F4DE ?")
        self.assertEqual(self.ec.output["color"], "#FF0000")

    def test_format_includes_room_alias(self):
        ec = make_plugin(format_active="{room_alias}: {participants}", room_alias="Family")
        with patch.object(ec, "_count_participants", return_value=3):
            ec.run()
        self.assertEqual(ec.output["full_text"], "Family: 3")


if __name__ == "__main__":
    unittest.main()
