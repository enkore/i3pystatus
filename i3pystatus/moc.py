import re

from i3pystatus import IntervalModule
from i3pystatus import formatp
from i3pystatus.core.command import run_through_shell
from i3pystatus.core.util import TimeWrapper


class Moc(IntervalModule):
    """
    Display various information from MOC (music on console)

    .. rubric:: Available formatters

    * `{status}` — current status icon (paused/playing/stopped)
    * `{song_elapsed}` — song elapsed time (mm:ss format)
    * `{song_length}` — total song duration (mm:ss format)
    * `{artist}` — artist
    * `{title}` — title
    * `{album}` — album
    * `{tracknumber}` — tracknumber
    * `{file}` — file or url name
    """

    settings = (
        ('format', 'formatp string'),
        ('format_not_running', 'Text to show if MOC is not running'),
        ('color', 'The color of the text'),
        ('color_not_running', 'The color of the text, when MOC is not running'),
        ('status', 'Dictionary mapping status to output'),
    )

    color = '#ffffff'
    color_not_running = '#ffffff'
    format = '{status} {song_elapsed}/{song_length} {artist} - {title}'
    format_not_running = 'Not running'
    interval = 1
    status = {
        'pause': '▷',
        'play': '▶',
        'stop': '◾',
    }

    on_leftclick = 'toggle_pause'
    on_rightclick = 'next_song'
    on_upscroll = 'next_song'
    on_downscroll = 'previous_song'

    def _moc_command(self, command):
        cmdline = 'mocp --{command}'.format(command=command)
        return run_through_shell(cmdline, enable_shell=True)

    def _query_moc(self):
        response = {}

        # Get raw information
        cmd = self._moc_command('info')

        # Now we make it useful
        if not cmd.rc:
            for line in cmd.out.splitlines():
                key, _, value = line.partition(': ')
                response[key] = value

        return response

    def run(self):
        response = self._query_moc()

        if response:
            fdict = {
                'album': response.get('Album', ''),
                'artist': response.get('Artist', ''),
                'file': response.get('File', ''),
                'song_elapsed': TimeWrapper(response.get('CurrentSec', 0)),
                'song_length': TimeWrapper(response.get('TotalSec', 0)),
                'status': self.status[response['State'].lower()],
                'title': response.get('SongTitle', ''),
                'tracknumber': re.match(r'(\d*).*', response.get('Title', '')).group(1) or 0,
            }

            self.data = fdict

            self.output = {
                'full_text': formatp(self.format, **self.data),
                'color': self.color,
            }
        else:
            if hasattr(self, "data"):
                del self.data

            self.output = {
                'full_text': self.format_not_running,
                'color': self.color_not_running,
            }

    def toggle_pause(self):
        self._moc_command('toggle-pause')

    def next_song(self):
        self._moc_command('next')

    def previous_song(self):
        self._moc_command('previous')
