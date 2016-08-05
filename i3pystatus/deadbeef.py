from i3pystatus import IntervalModule, formatp
from subprocess import check_output, CalledProcessError


class NotRunningException(Exception):
    pass


class StopException(Exception):
    pass


class ErrorException(Exception):
    pass


class DeaDBeeF(IntervalModule):
    """
    Display track currently playing in deadbeef for i3pystatus.
    fork from deadbeef of py3status by mrt-prodz

    Requires the `DeaDBeeF` player.

    .. rubric:: Available formatters
    * `{status}` —  player status
    * `{album}` —  album
    * `{artist}` —  artist
    * `{title}` —  title
    * `{elapsed}` —  elapsed time
    * `{length}` —  total length
    * `{bitrate}` —  bit rate
    * `{codec}` —  encode type

    @author jok
    """

    settings = (
        ("status", "Dictionary mapping pause, play and stop to output text"),
        ("format", "Format string"),
        ("format_not_running", "Text to show if deadbeef is not running"),
        ("format_stopped", "Text to show if deadbeef is stopped"),
        ("color", "Text color"),
        ("color_not_running", "Text color when deadbeef is not running"),
        ("color_stopped", "Text color when deadbeef is stopped"),
    )

    delimiter = '¥'
    color = "#FFFFFF"
    color_not_running = "#FFFFFF"
    color_stopped = "#FF0000"
    format = "{status} {artist} - {title}"
    format_not_running = "Not Running"
    format_stopped = "STOPPED"
    interval = 1
    status = {
        'paused': '▷',
        'playing': '▶',
        'stopped': '◾',
    }

    on_leftclick = "play_pause"
    on_rightclick = "next_song"

    def get_info(self):
        try:
            # check if we have deadbeef running
            check_output(['pidof', 'deadbeef'])
        except CalledProcessError:
            raise NotRunningException

        # get all properties using ¥ as delimiter
        info = check_output(['deadbeef',
                            '--nowplaying-tf',
                             self.delimiter.join(['%artist%',
                                                  '%title%',
                                                  '%album%',
                                                  '%length%',
                                                  '%playback_time%',
                                                  '%bitrate%',
                                                  '%codec%',
                                                  '%isplaying%',
                                                  '%ispaused%'])]).decode()

        if info == self.delimiter * 3 + "0:00" + self.delimiter * 5:
            raise StopException

        # split properties using special delimiter
        parts = info.split(self.delimiter)
        if len(parts) == 9:
            return parts
        else:
            raise ErrorException

    def run(self):
        try:
            parts = self.get_info()
            artist, title, album, length, elapsed, bitrate, codec, isplaying, ispaused = parts

            db_status = 'stopped'
            if isplaying == '1' and ispaused == '':
                db_status = 'playing'
            elif isplaying == '' and ispaused == '1':
                db_status = 'paused'

            p_dict = {
                "status": self.status[db_status],
                "artist": artist,
                "title": title,
                "album": album,
                "length": length,
                "elapsed": elapsed,
                "bitrate": bitrate,
                "codec": codec,
            }

            self.data = p_dict
            self.output = {
                "full_text": formatp(self.format, **p_dict).strip(),
                "color": self.color,
            }

        except NotRunningException:
            self.output = {
                "full_text": self.format_not_running,
                "color": self.color_not_running,
            }
            if hasattr(self, "data"):
                del self.data
            return

        except StopException:
            self.output = {
                "full_text": self.status['stopped'] + " " + self.format_stopped,
                "color": self.color_stopped,
            }
            if hasattr(self, "data"):
                del self.data
            return

        except ErrorException:
            self.output = {
                "full_text": "ERROR WITH DEADBEEF",
                "color": "#FF00000",
            }
            if hasattr(self, "data"):
                del self.data
            return

    @staticmethod
    def play_pause():

        try:
            check_output(['pidof', 'deadbeef'])
        except CalledProcessError:
            return

        check_output(['deadbeef', '--toggle-pause'])

    @staticmethod
    def next_song():

        try:
            check_output(['pidof', 'deadbeef'])
        except CalledProcessError:
            return

        check_output(['deadbeef', '--next'])
