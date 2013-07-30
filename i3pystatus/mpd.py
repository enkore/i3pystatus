
import socket

from i3pystatus import IntervalModule

class MPD(IntervalModule):
    """
    Displays various information from MPD (the music player daemon)

    Available formatters:
    * title (the title of the current song)
    * album (the album of the current song, can be an empty string (e.g. for online streams))
    * artist (can be empty, too)
    * playtime_h (Playtime, hours)
    * playtime_m (Playtime, minutes)
    * playtime_s (Playtime, seconds)
    * pos (Position of current song in playlist, one-based)
    * len (Length of current playlist)
    * status

    Left click on the module play/pauses, right click (un)mutes.
    """
    interval = 1

    settings = (
        ("host"),
        ("port", "MPD port"),
        "format",
        ("status", "Dictionary mapping pause, play and stop to output")
    )

    host = "localhost"
    port = 6600
    format = "{title} {status}"
    status = {
        "pause": "▷",
        "play": "▶",
        "stop": "◾",
    }

    vol = 100

    def _mpd_command(self, sock, command):
        sock.send((command + "\n").encode("utf-8"))
        reply = sock.recv(16384).decode("utf-8")
        replylines = reply.split("\n")[:-2]

        return dict(
            (line.split(": ", 1)[0], line.split(": ", 1)[1]) for line in replylines
        )

    def run(self):
        with socket.create_connection((self.host, self.port)) as s:
            s.recv(8192)
            fdict = {}

            status = self._mpd_command(s, "status")
            fdict["pos"] = int(status.get("song", 0))+1
            fdict["len"] = int(status["playlistlength"])
            fdict["status"] = self.status[status["state"]]

            currentsong = self._mpd_command(s, "currentsong")
            fdict["title"] = currentsong.get("Title", "")
            fdict["album"] = currentsong.get("Album", "")
            fdict["artist"] = currentsong.get("Artist", "")

            playtime = int(self._mpd_command(s, "stats")["playtime"])
            fdict["playtime_h"] = playtime // 3600
            fdict["playtime_m"] = (playtime % 3600) // 60
            fdict["playtime_s"] = (playtime % 3600) % 60

            self.output = {
                "full_text": self.format.format(**fdict).strip(),
            }

    def on_leftclick(self):
        with socket.create_connection(("localhost", self.port)) as s:
            s.recv(8192)
            
            self._mpd_command(s, "pause %i" % (0 if self._mpd_command(s, "status")["state"] == "pause" else 1))

    def on_rightclick(self):
        with socket.create_connection(("localhost", self.port)) as s:
            s.recv(8192)
            
            vol = int(self._mpd_command(s, "status")["volume"])
            if vol == 0:
                self._mpd_command(s, "setvol %i" % self.vol)
            else:
                self.vol = vol
                self._mpd_command(s, "setvol 0")
