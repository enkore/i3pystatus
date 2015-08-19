import os

from i3pystatus import IntervalModule, formatp
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
        ('color', 'The color of the text'),
    )

    color = '#909090'
    format = '{status} {song_elapsed}/{song_length} {artist} - {title}'
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
        status_dict = {}
        cmd = self._cmus_command('query')
        if not cmd.rc:
            status = cmd.out.split('\n')
            for item in status:
                split_item = item.split(' ')
                if split_item[0] in ['tag', 'set']:
                    key = '_'.join(split_item[:2])
                    val = ' '.join([x for x in split_item[2:]])
                    status_dict[key] = val
                else:
                    status_dict[split_item[0]] = ' '.join(split_item[1:])
        return status_dict

    def run(self):
        status = self._query_cmus()
        if not status:
            self.output = {
                'full_text': 'Not running',
                'color': self.color
            }
            return
        fdict = {
            'file': status.get('file', ''),
            'status': self.status[status['status']],
            'title': status.get('tag_title', ''),
            'stream': status.get('stream', ''),
            'album': status.get('tag_album', ''),
            'artist': status.get('tag_artist', ''),
            'tracknumber': status.get('tag_tracknumber', 0),
            'song_length': TimeWrapper(status.get('duration', 0)),
            'song_elapsed': TimeWrapper(status.get('position', 0)),
            'bitrate': int(status.get('bitrate', 0)),
        }

        if fdict['stream']:
            fdict['artist'], fdict[
                'title'] = _extract_artist_title(fdict['stream'])

        elif not fdict['title']:
            _, filename = os.path.split(fdict['file'])
            filebase, _ = os.path.splitext(filename)
            fdict['artist'], fdict['title'] = _extract_artist_title(filebase)

        fdict['title'] = fdict['title'].strip()
        fdict['artist'] = fdict['artist'].strip()

        self.output = {
            'full_text': formatp(self.format, **fdict),
            'color': self.color
        }

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
