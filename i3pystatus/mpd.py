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
        ("msg_error", "Discrete 'no mpd' error message"),
        ("color_error", "Color error message"),
        ("status", "Dictionary mapping pause, play and stop to output"),
        ("color", "The color of the text"),
        ("max_field_len", "Defines max length for in truncate_fields defined fields, if truncated, ellipsis are appended as indicator. It's applied *before* max_len. Value of 0 disables this."),
        ("max_len", "Defines max length for the hole string, if exceeding fields specefied in truncate_fields are truncated equaly. If truncated, ellipsis are appended as indicator. It's applied *after* max_field_len. Value of 0 disables this."),
        ("truncate_fields", "fields that will be truncated if exceeding max_field_len or max_len."),

    )

    host = "localhost"
    port = 6600
    s = None
    format = "{title} {status}"
    status = {
        "pause": "▷",
        "play": "▶",
        "stop": "◾",
    }
    color = "#FFFFFF"
    max_field_len = 25
    max_len = 100
    msg_error = "No_mpd"
    color_error = "#FFF000"
    truncate_fields = ("title", "album", "artist")
    on_leftclick = "switch_playpause"
    on_rightclick = "next_song"
    on_upscroll = on_rightclick
    on_downscroll = "previous_song"

    def _mpd_command(self, sock, command):
        try:
            sock.send((command + "\n").encode("utf-8"))
        except Exception as e:
            try:
                self.s = socket.create_connection((self.host, self.port))
            except socket.error as e:
                return None
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
        if status is not None:
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

            if self.max_field_len > 0:
                for key in self.truncate_fields:
                    if len(fdict[key]) > self.max_field_len:
                        fdict[key] = fdict[key][:self.max_field_len - 1] + "…"

            color_out = self.color
            full_text = formatp(self.format, **fdict).strip()
            full_text_len = len(full_text)
            if full_text_len > self.max_len and self.max_len > 0:
                shrink = floor((self.max_len - full_text_len) /
                               len(self.truncate_fields)) - 1

                for key in self.truncate_fields:
                    fdict[key] = fdict[key][:shrink] + "…"
            
                full_text = formatp(self.format, **fdict).strip()
        else:
            full_text = self.msg_error
            color_out = self.color_error

        self.output = {
            "full_text": full_text,
            "color": color_out,
        }

    def switch_playpause(self):
        try:
            self._mpd_command(self.s, "%s" %
                              ("play" if self._mpd_command(self.s, "status")["state"] in ["pause", "stop"] else "pause"))
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
