# -*- coding: utf-8 -*-
import shutil
import subprocess

from i3pystatus import IntervalModule, formatp


class Deadbeef(IntervalModule):
    """
    Plugin for DeaDBeeF music player.

    - Requires deadbeef >= 0.6.2

    The playing/paused detection is a bit wonky since you can't get the
    status directly from DB, so please do not use intervals shorter than 1s.

    Available formatters (uses :ref:`formatp`)

    * `{state}` — play, pause, stop mapped through the `status` dictionary
    * `{artist}` — artist of current song
    * `{title}` — title of current song
    * `{album}` — album of current song
    * `{band}` — gives "band", or "album artist" or "albumartist" or "artist",\
        whichever exists, in this order
    * `{composer}` — composer
    * `{track}` — (current song number
    * `{numtracks}` — number of tracks in current song's album
    * `{year}` — date or year
    * `{genre}` — genre
    * `{comment}` — comment
    * `{copyright}` — copyright
    * `{length}` — current song length (duration)
    * `{elapsed}` — elaped time of current song
    * `{filename}` — filename without path
    * `{fullname}` — full pathname/uri
    * `{dir}` — directory without path
    * `{fulldir}` — directory name with full path
    * `{channels}` — channel configuration (mono/stereo/..)
    * `{version}` — deadbeef version number

    """

    interval = 1.1

    settings = (
        ("format", "formatp string"),
        ("format_down", "String to use when DB is not running"),
        ("status", "Dictionary mapping pause, play and stop to output"),
        ("color", "Text color"),
        ("color_down", "Text color when DB is not running"),
    )

    format = "{state} {elapsed} {artist} - {title}"
    color = "#00dd00"

    format_down = "DeaDBeeF"
    color_down = "#dd0000"

    # format when stopped is allways just "{state}" i.e. status["stop"]
    status = {
        "pause": u"▷",
        "play": u"▶",
        "stop": u"◾ DeaDBeeF",
    }

    on_rightclick = "db_quit"
    on_leftclick = "db_play_pause"
    on_upscroll = "db_prev"
    on_downscroll = "db_next"

    def init(self):
        self.elapsed = "0:00"
        db_dict = {
            "state": "{state}",
            "artist": "%a",
            "title": "%t",
            "album": "%b",
            "band": "%B",
            "composer": "%C",
            "track": "%n",
            "numtracks": "%N",
            "year": "%y",
            "genre": "%g",
            "comment": "%c",
            "copyright": "%r",
            "length": "%l",
            "elapsed": "%e",
            "filename": "%f",
            "fullname": "%F",
            "dir": "%d",
            "fulldir": "%D",
            "channels": "%Z",
            "version": "%V",
        }
        self.db_format = formatp(self.format, **db_dict).strip()

    def run(self):
        if not self.db_running():
            self.output = {
                "full_text": self.format_down,
                "color": self.color_down,
            }
            return

        try:
            command = ['deadbeef', '--nowplaying', '%e ' + self.db_format]
            db = subprocess.Popen(command, shell=False,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)
            db_out, db_err = db.communicate()
        except OSError as e:
            self.output = {
                "full_text": "Error: " + e.strerror,
                "color": "#ff0000",
            }
            return
        except subprocess.CalledProcessError as e:
            self.output = {
                "full_text": "Error: " + e.output,
                "color": "#ff0000",
            }
            return
        db_out = db_out.decode("UTF-8").replace("\n", " ").strip()

        if db_out == "nothing":
            self.output = {
                "full_text": self.status["stop"],
                "color": self.color,
            }
            return

        elapsed, db_out = db_out.split(" ", 1)
        if elapsed == self.elapsed:
            state = "pause"
        else:
            state = "play"
            self.elapsed = elapsed

        self.output = {
            "full_text": db_out.format(state=self.status[state]).strip(),
            "color": self.color,
        }

    def db_running(self):
        command = "pidof deadbeef"
        pidof = subprocess.Popen(command.split(), shell=False,
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        pidof.communicate()
        return False if pidof.returncode != 0 else True

    def db_quit(self):
        command = "deadbeef"
        if self.db_running():
            command += " --quit"
        subprocess.Popen(command.split())

    def db_play_pause(self):
        command = "deadbeef --play-pause"
        subprocess.Popen(command.split())

    def db_prev(self):
        if self.db_running():
            command = "deadbeef --prev"
            subprocess.Popen(command.split())

    def db_next(self):
        if self.db_running():
            command = "deadbeef --next"
            subprocess.Popen(command.split())
