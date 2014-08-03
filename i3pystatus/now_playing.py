
import functools
from os.path import basename

import dbus

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


class NowPlaying(IntervalModule):
    """
    Shows currently playing track information, supports most media players

    Available formatters (uses `formatp`_)

    * `{title}` — (the title of the current song)
    * `{album}` — (the album of the current song, can be an empty string (e.g. for online streams))
    * `{artist}` — (can be empty, too)
    * `{filename}` — (file name with out extension and path; empty unless title is empty)
    * `{song_elapsed}` — (Position in the currently playing song, uses `TimeWrapper`_, default is `%m:%S`)
    * `{song_length}` — (Length of the current song, same as song_elapsed)
    * `{status}` — (play, pause, stop mapped through the `status` dictionary)
    * `{volume}` — (Volume)

    Left click on the module play/pauses, right click goes to the next track.

    Requires python-dbus available from every distros' package manager.
    """

    interval = 1

    settings = (
        ("player", "Player name"),
        ("status", "Dictionary mapping pause, play and stop to output text"),
        ("color", "Text color"),
        ("format", "formatp string"),

    )
    required = ("player",)

    format = "{title} {status}"
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
    color = "#FFFFFF"

    def get_player(self):
        return dbus.SessionBus().get_object("org.mpris.MediaPlayer2." + self.player, "/org/mpris/MediaPlayer2")

    def run(self):
        try:
            player = self.get_player()
        except dbus.exceptions.DBusException:
            self.output = {
                "full_text": "now_playing: d-bus error",
                "color": "#ff0000",
            }
            return

        properties = dbus.Interface(player, "org.freedesktop.DBus.Properties")
        get_prop = functools.partial(properties.Get, "org.mpris.MediaPlayer2.Player")
        currentsong = get_prop("Metadata")

        fdict = {
            "status": self.status[self.statusmap[get_prop("PlaybackStatus")]],
            "len": 0, # TODO: Use optional(!) TrackList interface for this to gain 100 % mpd<->now_playing compat
            "pos": 0,
            "volume": int(get_prop("Volume") * 100),

            "title":currentsong.get("xesam:title", ""),
            "album": currentsong.get("xesam:album", ""),
            "artist": ", ".join(currentsong.get("xesam:artist", "")),
            "song_length": TimeWrapper(currentsong.get("mpris:length") / 1000**2),
            "song_elapsed": TimeWrapper(get_prop("Position") / 1000**2),
            "filename": "",
        }

        if not fdict["title"]:
            fdict["filename"] = '.'.join(
                basename(currentsong["xesam:url"]).split('.')[:-1])

        self.output = {
            "full_text": formatp(self.format, **fdict).strip(),
            "color": self.color,
        }

    def on_leftclick(self):
        self.get_player().PlayPause()

    def on_rightclick(self):
        self.get_player().Next()
