from os.path import basename

import dbus

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


class Dbus:
    obj_dbus = "org.freedesktop.DBus"
    path_dbus = "/org/freedesktop/DBus"
    obj_player = "org.mpris.MediaPlayer2"
    path_player = "/org/mpris/MediaPlayer2"
    intf_props = obj_dbus + ".Properties"
    intf_player = obj_player + ".Player"


class NoPlayerException(Exception):
    pass


class NowPlaying(IntervalModule):
    """
    Shows currently playing track information. Supports media players that \
conform to the Media Player Remote Interfacing Specification.

    * Requires ``python-dbus`` from your distro package manager, or \
``dbus-python`` from PyPI.

    Left click on the module to play/pause, and right click to go to the next \
track.

    .. rubric:: Available formatters (uses :ref:`formatp`)

    * `{title}` — (the title of the current song)
    * `{album}` — (the album of the current song, can be an empty string \
(e.g. for online streams))
    * `{artist}` — (can be empty, too)
    * `{filename}` — (file name with out extension and path; empty unless \
title is empty)
    * `{song_elapsed}` — (position in the currently playing song, uses \
:ref:`TimeWrapper`, default is `%m:%S`)
    * `{song_length}` — (length of the current song, same as song_elapsed)
    * `{status}` — (play, pause, stop mapped through the `status` dictionary)
    * `{volume}` — (volume)

    .. rubric:: Available callbacks

    * ``playpause`` — Plays if paused or stopped, otherwise pauses.
    * ``next_song`` — Goes to next track in the playlist.
    * ``player_command`` — Invoke a command with the `MediaPlayer2.Player` \
interface. The method name and its arguments are appended as list elements.
    * ``player_prop`` — Get or set a property of the `MediaPlayer2.Player` \
interface. Append the property name to get, or the name and a value to set.

    `MediaPlayer2.Player` methods and properties are documented at \
https://specifications.freedesktop.org/mpris-spec/latest/Player_Interface.html

    Your player may not support the full interface.

    Example module registration with callbacks:

    ::

        status.register("now_playing",
            on_leftclick=["player_command", "PlayPause"],
            on_rightclick=["player_command", "Stop"],
            on_middleclick=["player_prop", "Shuffle", True],
            on_upscroll=["player_command", "Seek", -10000000],
            on_downscroll=["player_command", "Seek", +10000000])

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
    on_upscroll = 'volume_up'
    on_downscroll = 'volume_down'

    player = None
    old_player = None

    def find_player(self):
        obj = dbus.SessionBus().get_object(Dbus.obj_dbus, Dbus.path_dbus)

        def get_players(methodname):
            method = obj.get_dbus_method(methodname, Dbus.obj_dbus)
            return [a for a in method() if a.startswith(Dbus.obj_player + ".")]

        players = get_players('ListNames')
        if not players:
            players = get_players('ListActivatableNames')
        if self.old_player in players:
            return self.old_player
        if not players:
            raise NoPlayerException()
        self.old_player = players[0]
        return players[0]

    def get_player(self):
        if self.player:
            player = Dbus.obj_player + "." + self.player
            try:
                return dbus.SessionBus().get_object(player, Dbus.path_player)
            except dbus.exceptions.DBusException:
                raise NoPlayerException()
        else:
            player = self.find_player()
            return dbus.SessionBus().get_object(player, Dbus.path_player)

    def run(self):
        try:
            currentsong = self.get_player_prop("Metadata")

            fdict = {
                "status": self.status[self.statusmap[
                    self.get_player_prop("PlaybackStatus")]],
                # TODO: Use optional(!) TrackList interface for this to
                # gain 100 % mpd<->now_playing compat
                "len": 0,
                "pos": 0,
                "volume": int(self.get_player_prop("Volume", 0) * 100),

                "title": currentsong.get("xesam:title", ""),
                "album": currentsong.get("xesam:album", ""),
                "artist": ", ".join(currentsong.get("xesam:artist", "")),
                "song_length": TimeWrapper(
                    (currentsong.get("mpris:length") or 0) / 1000 ** 2),
                "song_elapsed": TimeWrapper(
                    (self.get_player_prop("Position") or 0) / 1000 ** 2),
                "filename": "",
            }

            if not fdict["title"]:
                fdict["filename"] = '.'.join(
                    basename((currentsong.get("xesam:url") or "")).
                    split('.')[:-1])

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
        self.player_command('PlayPause')

    def next_song(self):
        self.player_command('Next')

    def volume_up(self):
        self.set_player_prop('Volume', self.volume + 1.0)

    def volume_down(self):
        self.set_player_prop('Volume', self.volume - 1.0)

    @property
    def volume(self):
        return self.get_player_prop('Volume')

    def player_command(self, command, *args):
        try:
            interface = dbus.Interface(self.get_player(), Dbus.intf_player)
            return getattr(interface, command)(*args)
        except NoPlayerException:
            return
        except dbus.exceptions.DBusException:
            return

    def get_player_prop(self, name, default=None):
        properties = dbus.Interface(self.get_player(), Dbus.intf_props)
        try:
            return properties.Get(Dbus.intf_player, name)
        except dbus.exceptions.DBusException:
            return default

    def set_player_prop(self, name, value):
        properties = dbus.Interface(self.get_player(), Dbus.intf_props)
        try:
            return properties.Set(Dbus.intf_player, name, value)
        except dbus.exceptions.DBusException as e:
            self.logger.error('error setting player property: %s', e)
            return

    def player_prop(self, name, value=None):
        try:
            properties = dbus.Interface(self.get_player(), Dbus.intf_props)
            # None/null/nil implies get because it's not a valid DBus datatype.
            if value is None:
                return properties.Get(Dbus.intf_player, name)
            else:
                properties.Set(Dbus.intf_player, name, value)
        except NoPlayerException:
            return
        except dbus.exceptions.DBusException:
            return
