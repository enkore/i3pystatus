from collections import defaultdict
import socket
from os.path import basename
from math import floor

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


class MPD(IntervalModule):
    """
    Displays various information from MPD (the music player daemon)

    .. rubric:: Available formatters (uses :ref:`formatp`)

    * `{title}` — (the title of the current song)
    * `{album}` — (the album of the current song, can be an empty string \
(e.g. for online streams))
    * `{artist}` — (can be empty, too)
    * `{album_artist}` — (can be empty)
    * `{filename}` — (file name with out extension and path; empty unless \
title is empty)
    * `{song_elapsed}` — (Position in the currently playing song, uses \
:ref:`TimeWrapper`, default is `%m:%S`)
    * `{song_length}` — (Length of the current song, same as song_elapsed)
    * `{pos}` — (Position of current song in playlist, one-based)
    * `{len}` — (Songs in playlist)
    * `{status}` — (play, pause, stop mapped through the `status` dictionary)
    * `{bitrate}` — (Current bitrate in kilobit/s)
    * `{volume}` — (Volume set in MPD)

    .. rubric:: Available callbacks

    * ``switch_playpause`` — Plays if paused or stopped, otherwise pauses. \
Emulates ``mpc toggle``.
    * ``stop`` — Stops playback. Emulates ``mpc stop``.
    * ``next_song`` — Goes to next track in the playlist. Emulates ``mpc \
next``.
    * ``previous_song`` — Goes to previous track in the playlist. Emulates \
``mpc prev``.
    * ``mpd_command`` — Send a command directly to MPD's socket. The command \
is the second element of the list. Documentation for available commands can \
be found at https://www.musicpd.org/doc/protocol/command_reference.html

    Example module registration with callbacks:

    ::

        status.register("mpd",
            on_leftclick="switch_playpause",
            on_rightclick=["mpd_command", "stop"],
            on_middleclick=["mpd_command", "shuffle"],
            on_upscroll=["mpd_command", "seekcur -10"],
            on_downscroll=["mpd_command", "seekcur +10"])

    Note that ``next_song`` and ``previous_song``, and their ``mpd_command`` \
equivalents, are ignored while mpd is stopped.

    """

    interval = 1

    settings = (
        ("host"),
        ("port", "MPD port. If set to 0, host will we interpreted as a Unix \
socket."),
        ("format", "formatp string"),
        ("status", "Dictionary mapping pause, play and stop to output"),
        ("color", "The color of the text"),
        ("color_map", "The mapping from state to color of the text"),
        ("max_field_len", "Defines max length for in truncate_fields defined \
fields, if truncated, ellipsis are appended as indicator. It's applied \
*before* max_len. Value of 0 disables this."),
        ("max_len", "Defines max length for the hole string, if exceeding \
fields specefied in truncate_fields are truncated equaly. If truncated, \
ellipsis are appended as indicator. It's applied *after* max_field_len. Value \
of 0 disables this."),
        ("truncate_fields", "fields that will be truncated if exceeding \
max_field_len or max_len."),
        ("hide_inactive", "Hides status information when MPD is not running"),
        ("password", "A password for access to MPD. (This is sent in \
cleartext to the server.)"),
    )

    host = "localhost"
    port = 6600
    password = None
    s = None
    format = "{title} {status}"
    status = {
        "pause": "▷",
        "play": "▶",
        "stop": "◾",
    }
    color = "#FFFFFF"
    color_map = {}
    max_field_len = 25
    max_len = 100
    truncate_fields = ("title", "album", "artist", "album_artist")
    hide_inactive = False
    on_leftclick = "switch_playpause"
    on_rightclick = "next_song"
    on_upscroll = on_rightclick
    on_downscroll = "previous_song"

    def _mpd_command(self, sock, command):
        try:
            sock.send((command + "\n").encode("utf-8"))
        except Exception as e:
            if self.port != 0:
                self.s = socket.create_connection((self.host, self.port))
            else:
                self.s = socket.socket(family=socket.AF_UNIX)
                self.s.connect(self.host)
            sock = self.s
            sock.recv(8192)
            if self.password is not None:
                sock.send('password "{}"\n'.format(self.password).
                          encode("utf-8"))
                sock.recv(8192)
            sock.send((command + "\n").encode("utf-8"))
        try:
            reply = sock.recv(16384).decode("utf-8", "replace")
            replylines = reply.split("\n")[:-2]

            return dict(
                (line.split(": ", 1)) for line in replylines
            )
        except Exception as e:
            return None

    def run(self):
        try:
            status = self._mpd_command(self.s, "status")
            playback_state = status["state"]
            if playback_state == "stop":
                currentsong = {}
            else:
                currentsong = self._mpd_command(self.s, "currentsong") or {}
        except Exception:
            if self.hide_inactive:
                self.output = {
                    "full_text": ""
                }
            if hasattr(self, "data"):
                del self.data
            return

        fdict = {
            "pos": int(status.get("song", 0)) + 1,
            "len": int(status.get("playlistlength", 0)),
            "status": self.status[playback_state],
            "volume": int(status.get("volume", 0)),

            "title": currentsong.get("Title", ""),
            "album": currentsong.get("Album", ""),
            "artist": currentsong.get("Artist", ""),
            "album_artist": currentsong.get("AlbumArtist", ""),
            "song_length": TimeWrapper(currentsong.get("Time", 0)),
            "song_elapsed": TimeWrapper(float(status.get("elapsed", 0))),
            "bitrate": int(status.get("bitrate", 0)),
        }

        if not fdict["title"] and "file" in currentsong:
            fdict["filename"] = '.'.join(
                basename(currentsong["file"]).split('.')[:-1])
        else:
            fdict["filename"] = ""

        if self.max_field_len > 0:
            for key in self.truncate_fields:
                if len(fdict[key]) > self.max_field_len:
                    fdict[key] = fdict[key][:self.max_field_len - 1] + "…"

        self.data = fdict
        full_text = formatp(self.format, **fdict).strip()
        full_text_len = len(full_text)
        if full_text_len > self.max_len and self.max_len > 0:
            shrink = floor((self.max_len - full_text_len)
                           / len(self.truncate_fields)) - 1

            for key in self.truncate_fields:
                fdict[key] = fdict[key][:shrink] + "…"

            full_text = formatp(self.format, **fdict).strip()
        color_map = defaultdict(lambda: self.color, self.color_map)
        self.output = {
            "full_text": full_text,
            "color": color_map[playback_state],
        }

    def switch_playpause(self):
        try:
            self._mpd_command(self.s, "play"
                              if self._mpd_command(self.s, "status")["state"]
                              in ["pause", "stop"] else "pause 1")
        except Exception as e:
            pass

    def stop(self):
        try:
            self._mpd_command(self.s, "stop")
        except Exception as e:
            pass

    def next_song(self):
        try:
            self._mpd_command(self.s, "next")
        except Exception as e:
            pass

    def previous_song(self):
        try:
            self._mpd_command(self.s, "previous")
        except Exception as e:
            pass

    def mpd_command(self, command):
        try:
            self._mpd_command(self.s, command)
        except Exception as e:
            pass
