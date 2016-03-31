import os

from i3pystatus import formatp
from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell
from i3pystatus.core.util import TimeWrapper


def _extract_artist_title(input):
    artist, title = (input.split('-') + [''])[:2]
    return artist.strip(), title.strip()


class Cmus(IntervalModule):
    """
    Gets the status and current song info using cmus-remote

    .. rubric:: Available formatters

    * `{status}` — current status icon (paused/playing/stopped)
    * `{song_elapsed}` — song elapsed time (mm:ss format)
    * `{song_length}` — total song duration (mm:ss format)
    * `{artist}` — artist
    * `{title}` — title
    * `{album}` — album
    * `{tracknumber}` — tracknumber
    * `{file}` — file or url name
    * `{stream}` — song name from stream
    * `{bitrate}` — bitrate
    """

    settings = (
        ('format', 'formatp string'),
        ('format_not_running', 'Text to show if cmus is not running'),
        ('color', 'The color of the text'),
        ('color_not_running', 'The color of the text, when cmus is not running'),
        ('status', 'Dictionary mapping status to output'),
    )

    color = '#ffffff'
    color_not_running = '#ffffff'
    format = '{status} {song_elapsed}/{song_length} {artist} - {title}'
    format_not_running = 'Not running'
    interval = 1
    status = {
        'paused': '▷',
        'playing': '▶',
        'stopped': '◾',
    }

    on_leftclick = 'playpause'
    on_rightclick = 'next_song'
    on_upscroll = 'next_song'
    on_downscroll = 'previous_song'

    def _cmus_command(self, command):
        cmdline = 'cmus-remote --{command}'.format(command=command)
        return run_through_shell(cmdline, enable_shell=True)

    def _query_cmus(self):
        response = {}
        cmd = self._cmus_command('query')

        if not cmd.rc:
            for line in cmd.out.splitlines():
                category, _, category_value = line.partition(' ')
                if category in ('set', 'tag'):
                    key, _, value = category_value.partition(' ')
                    key = '_'.join((category, key))
                    response[key] = value
                else:
                    response[category] = category_value

        return response

    def run(self):
        response = self._query_cmus()
        if response:
            fdict = {
                'file': response.get('file', ''),
                'status': self.status[response['status']],
                'title': response.get('tag_title', ''),
                'stream': response.get('stream', ''),
                'album': response.get('tag_album', ''),
                'artist': response.get('tag_artist', ''),
                'tracknumber': response.get('tag_tracknumber', 0),
                'song_length': TimeWrapper(response.get('duration', 0)),
                'song_elapsed': TimeWrapper(response.get('position', 0)),
                'bitrate': int(response.get('bitrate', 0)),
            }

            if fdict['stream']:
                fdict['artist'], fdict['title'] = _extract_artist_title(fdict['stream'])
            elif not fdict['title']:
                filename = os.path.basename(fdict['file'])
                filebase, _ = os.path.splitext(filename)
                fdict['artist'], fdict['title'] = _extract_artist_title(filebase)
            self.data = fdict
            self.output = {"full_text": formatp(self.format, **fdict),
                           "color": self.color}

        else:
            if hasattr(self, "data"):
                del self.data
            self.output = {"full_text": self.format_not_running,
                           "color": self.color_not_running}

    def playpause(self):
        status = self._query_cmus().get('status', '')
        if status == 'playing':
            self._cmus_command('pause')
        if status == 'paused':
            self._cmus_command('play')
        if status == 'stopped':
            self._cmus_command('play')

    def next_song(self):
        self._cmus_command('next')

    def previous_song(self):
        self._cmus_command('prev')
