import socket
from os.path import basename

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


class MPD(IntervalModule):
    """
    Displays various information from MPD (the music player daemon)

    Available formatters (uses :ref:`formatp`)

    * `{title}` — (the title of the current song)
    * `{album}` — (the album of the current song, can be an empty string (e.g. for online streams))
    * `{artist}` — (can be empty, too)
    * `{filename}` — (file name with out extension and path; empty unless title is empty)
    * `{song_elapsed}` — (Position in the currently playing song, uses :ref:`TimeWrapper`, default is `%m:%S`)
    * `{song_length}` — (Length of the current song, same as song_elapsed)
    * `{pos}` — (Position of current song in playlist, one-based)
    * `{len}` — (Songs in playlist)
    * `{status}` — (play, pause, stop mapped through the `status` dictionary)
    * `{bitrate}` — (Current bitrate in kilobit/s)
    * `{volume}` — (Volume set in MPD)

    Left click on the module play/pauses, right click (un)mutes.
    """

    interval = 1

    settings = (
        ("host"),
        ("port", "MPD port"),
        ("format", "formatp string"),
        ("format_short", "formatp string for i3bars short_text option"),
        ("status", "Dictionary mapping pause, play and stop to output"),
        ("color", "The color of the text"),
        ("short_max_len", "maximale length for format_short, string will be truncated and ellipsis willl be placed as indicator, disabled if zero")
    )

    host = "localhost"
    port = 6600
    s = None
    format = "{title} {status}"
    format_short = "{title}"
    status = {
        "pause": "▷",
        "play": "▶",
        "stop": "◾",
    }
    color = "#FFFFFF"
    short_max_len = 0

    def _mpd_command(self, sock, command):
        try:
            sock.send((command + "\n").encode("utf-8"))
        except Exception as e:
            self.s = socket.create_connection((self.host, self.port))
            sock = self.s
            sock.recv(8192)
            sock.send((command + "\n").encode("utf-8"))
        try:
            reply = sock.recv(16384).decode("utf-8")
            replylines = reply.split("\n")[:-2]

            return dict(
                (line.split(": ", 1)) for line in replylines
            )
        except Exception as e:
            return None

    def run(self):
        status = self._mpd_command(self.s, "status")
        currentsong = self._mpd_command(self.s, "currentsong")
        fdict = {
            "pos": int(status.get("song", 0)) + 1,
            "len": int(status["playlistlength"]),
            "status": self.status[status["state"]],
            "volume": int(status["volume"]),

                "title": currentsong.get("Title", ""),
            "album": currentsong.get("Album", ""),
            "artist": currentsong.get("Artist", ""),
            "song_length": TimeWrapper(currentsong.get("Time", 0)),
            "song_elapsed": TimeWrapper(float(status.get("elapsed", 0))),
            "bitrate": int(status.get("bitrate", 0)),

        }
        if not fdict["title"] and "filename" in fdict:
            fdict["filename"] = '.'.join(
                basename(currentsong["file"]).split('.')[:-1])
        else:
            fdict["filename"] = ""

        short_text = formatp(self.format_short, **fdict).strip()
        if len(short_text) > self.short_max_len and self.short_max_len:
            short_text = short_text[:self.short_max_len] + "…"
        self.output = {
            "full_text": formatp(self.format, **fdict).strip(),
            "short_text": short_text,
            "color": self.color,
        }

    def on_leftclick(self):
        try:
            self._mpd_command(self.s, "%s" %
                    ("play" if self._mpd_command(self.s, "status")["state"] in ["pause", "stop"] else "pause"))
        except Exception as e:
            pass

    def on_rightclick(self):
        try:
            self._mpd_command(self.s, "next")
        except Exception as e:
            pass

    def on_upscroll(self):
        try:
            self._mpd_command(self.s, "next")
        except Exception as e:
            pass

    def on_downscroll(self):
        try:
            self._mpd_command(self.s, "previous")
        except Exception as e:
            pass
