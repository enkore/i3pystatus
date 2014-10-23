import os

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper
import subprocess


class Cmus(IntervalModule):

    """
    gets the status and current song info using cmus-remote
    """

    settings = (
        'format',
        'color'
    )
    color = "#909090"
    format = "{status} {song_elapsed}/{song_length} {artist}-{title}"
    status_text = ''
    interval = 1
    status = {
        "paused": "▷",
        "playing": "▶",
        "stopped": "◾",
    }

    def _cmus_command(self, command):
        p = subprocess.Popen('cmus-remote --{command}'.format(command=command), shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        return p.communicate()

    def _query_cmus(self):
        status_dict = {}
        status, error = self._cmus_command('query')
        status = status.decode('utf-8').split('\n')
        if status != b'cmus-remote: cmus is not running\n':
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
        fdict = {
            'file': status.get('file', ''),
            'status': self.status[status["status"]],
            'title': status.get('tag_title', ''),
            'stream': status.get('stream', ''),
            'album': status.get('tag_album', ''),
            'artist': status.get('tag_artist', ''),
            'tracknumber': status.get('tag_tracknumber', 0),
            'song_length': TimeWrapper(status.get('duration', 0)),
            'song_elapsed': TimeWrapper(status.get('position', 0)),
            'bitrate': int(status.get("bitrate", 0)),
        }

        if fdict['stream']:
            fdict['artist'], fdict['title'] = (
                fdict['stream'].split('-') + [''] * 2)[:2]

        elif not fdict['title']:
            _, filename = os.path.split(fdict['file'])
            filebase, _ = os.path.splitext(filename)
            fdict['artist'], fdict['title'] = (
                filebase.split('-') + [''] * 2)[:2]

        self.output = {
            "full_text": formatp(self.format, **fdict),
            "color": self.color
        }

    def on_leftclick(self):
        status = self._query_cmus().get('status', '')
        if status == 'playing':
            self._cmus_command('pause')
        if status == 'paused':
            self._cmus_command('play')
        if status == 'stopped':
            self._cmus_command('play')

    def on_rightclick(self):
        self._cmus_command("next")

    def on_upscroll(self):
        self._cmus_command("next")

    def on_downscroll(self):
        self._cmus_command("prev")
