
import functools
from os.path import basename

import dbus

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


class NoPlayerException(Exception):
    pass


class NowPlaying(IntervalModule):
    """
    Shows currently playing track information, supports most media players

    * Requires python-dbus available from every distros' package manager.

    Left click on the module play/pauses, right click goes to the next track.

    .. rubric:: Available formatters (uses :ref:`formatp`)

    * `{title}` — (the title of the current song)
    * `{album}` — (the album of the current song, can be an empty string (e.g. for online streams))
    * `{artist}` — (can be empty, too)
    * `{filename}` — (file name with out extension and path; empty unless title is empty)
    * `{song_elapsed}` — (position in the currently playing song, uses :ref:`TimeWrapper`, default is `%m:%S`)
    * `{song_length}` — (length of the current song, same as song_elapsed)
    * `{status}` — (play, pause, stop mapped through the `status` dictionary)
    * `{volume}` — (volume)
    """

    interval = 1

    settings = (
        ("player", "Player name. If not set, compatible players will be \
                    detected automatically."),
        ("status", "Dictionary mapping pause, play and stop to output text"),
        ("format", "formatp string"),
        ("color", "Text color"),
        ("format_no_player", "Text to show if no player is detected"),
        ("color_no_player", "Text color when no player is detected"),
        ("hide_no_player", "Hide output if no player is detected"),
    )

    hide_no_player = True
    format_no_player = "No Player"
    color_no_player = "#ffffff"

    format = "{title} {status}"
    color = "#ffffff"
    status = {
        "pause": "▷",
        "play": "▶",
        "stop": "◾",
    }
    statusmap = {
        "Playing": "play",
        "Paused": "pause",
        "Stopped": "stop",
    }

    on_leftclick = "playpause"
    on_rightclick = "next_song"

    player = None
    old_player = None

    def find_player(self):
        players = [a for a in dbus.SessionBus().get_object("org.freedesktop.DBus", "/org/freedesktop/DBus").ListNames() if a.startswith("org.mpris.MediaPlayer2.")]
        if self.old_player in players:
            return self.old_player
        if not players:
            raise NoPlayerException()
        self.old_player = players[0]
        return players[0]

    def get_player(self):
        if self.player:
            player = "org.mpris.MediaPlayer2." + self.player
            try:
                return dbus.SessionBus().get_object(player, "/org/mpris/MediaPlayer2")
            except dbus.exceptions.DBusException:
                raise NoPlayerException()
        else:
            player = self.find_player()
            return dbus.SessionBus().get_object(player, "/org/mpris/MediaPlayer2")

    def run(self):
        try:
            player = self.get_player()
            properties = dbus.Interface(player, "org.freedesktop.DBus.Properties")
            get_prop = functools.partial(properties.Get, "org.mpris.MediaPlayer2.Player")
            currentsong = get_prop("Metadata")

            fdict = {
                "status": self.status[self.statusmap[get_prop("PlaybackStatus")]],
                "len": 0,  # TODO: Use optional(!) TrackList interface for this to gain 100 % mpd<->now_playing compat
                "pos": 0,
                "volume": int(get_prop("Volume") * 100),

                "title": currentsong.get("xesam:title", ""),
                "album": currentsong.get("xesam:album", ""),
                "artist": ", ".join(currentsong.get("xesam:artist", "")),
                "song_length": TimeWrapper((currentsong.get("mpris:length") or 0) / 1000 ** 2),
                "song_elapsed": TimeWrapper((get_prop("Position") or 0) / 1000 ** 2),
                "filename": "",
            }

            if not fdict["title"]:
                fdict["filename"] = '.'.join(
                    basename((currentsong.get("xesam:url") or "")).split('.')[:-1])

            self.data = fdict
            self.output = {
                "full_text": formatp(self.format, **fdict).strip(),
                "color": self.color,
            }

        except NoPlayerException:
            if self.hide_no_player:
                self.output = None
            else:
                self.output = {
                    "full_text": self.format_no_player,
                    "color": self.color_no_player,
                }
            if hasattr(self, "data"):
                del self.data
            return

        except dbus.exceptions.DBusException as e:
            if self.hide_no_player:
                self.output = None
            else:
                self.output = {
                    "full_text": "DBus error: " + e.get_dbus_message(),
                    "color": "#ff0000",
                }
            if hasattr(self, "data"):
                del self.data
            return

    def playpause(self):
        try:
            dbus.Interface(self.get_player(), "org.mpris.MediaPlayer2.Player").PlayPause()
        except NoPlayerException:
            return
        except dbus.exceptions.DBusException:
            return

    def next_song(self):
        try:
            dbus.Interface(self.get_player(), "org.mpris.MediaPlayer2.Player").Next()
        except NoPlayerException:
            return
        except dbus.exceptions.DBusException:
            return
