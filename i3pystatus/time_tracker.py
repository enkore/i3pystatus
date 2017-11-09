from __future__ import print_function, unicode_literals

__author__ = "Fedor Marchenko"
__email__ = "mfs90@mail.ru"
__date__ = "Dec 28, 2016"

from time import time
import json
import os

from i3pystatus import IntervalModule


class TimeTracker(IntervalModule):
    """
    TimeTracker for track you time
    """
    interval = 5
    _start = None
    _stop = None
    _pauses = []
    _time = 0.0

    _colors = {
        'stop': '#FFFFFF',
        'run': '#41A6E4',
        'pause': '#00FF00'
    }
    _format = '\u23F1: {status}{time:.3f} hours.'
    _data_file = '/tmp/time_tracker.json'

    def __init__(self, *args, **kwargs):
        """ Initial data from JSON file and handle mouse click events """
        super(TimeTracker, self).__init__(*args, **kwargs)
        self.on_leftclick = self.leftclick_callback
        self.on_rightclick = self.rightclick_callback
        self.read_data()

    @property
    def is_run(self):
        """ Return True status for timer if running """
        return self._start and not self._stop

    @property
    def is_pause(self):
        """ Return True status for timer if paused """
        return self._start and self._stop

    def read_data(self):
        """ Read timer status from JSON file """
        data = {}
        if os.path.exists(self._data_file):
            with open(self._data_file, 'r') as fin:
                data = json.load(fin)
        if data:
            self._start = data.get('start')
            self._stop = data.get('stop')
            self._pauses = data.get('pauses', [])

    def wrire_date(self):
        """ Write timer status to JSON file """
        with open(self._data_file, 'w+') as fout:
            json.dump(
                {
                    'start': self._start,
                    'stop': self._stop,
                    'pauses': self._pauses
                },
                fout
            )

    def pauses_time(self):
        """ Return sum pauses time in seconds. """
        return sum(map(
            lambda x: x[1] - x[0], filter(lambda x: len(x) > 1, self._pauses)
        ))

    def run(self):
        self.output = {
            'color': self._colors['stop']
        }
        if self.is_run:
            self._time = (time() - self._start)
            self.output['color'] = self._colors['run']
        elif self.is_pause:
            self._time = (self._stop - self._start)
            self.output['color'] = self._colors['pause']
        self._time -= self.pauses_time()
        self.output['full_text'] = self._format.format(
            time=round(self._time / 60 / 60, 3),
            status='\u25B6 ' if self.is_run
            else '\u23F8 ' if self.is_pause else ''
        )
        self.wrire_date()

    def leftclick_callback(self, *args):
        """ Callback for event mouse left button click """
        if self.is_run:
            self._stop = time()
        elif self.is_pause:
            self._pauses.append((self._stop, time()))
            self._stop = None
        else:
            self._start = time()
            self._stop = None
            self._time = 0.0

    def rightclick_callback(self, *args):
        """ Callback for event mouse right button click """
        if self.is_pause:
            self._start = None
            self._stop = None
            self._time = 0.0
            self._pauses = []
