import os
import subprocess
import locale

from datetime import datetime, timedelta

from i3pystatus import IntervalModule


class Pomodoro(IntervalModule):

    """
    This plugin shows Pomodoro timer.

    Left click starts/restarts timer.
    Right click stops it.
    """

    settings = (
        ('sound',
         'Path to sound file to play as alarm. Played by "aplay" utility'),
        ('pomodoro_duration',
         'Working (pomodoro) interval duration in seconds'),
        ('break_duration', 'Short break duration in seconds'),
        ('long_break_duration', 'Long break duration in seconds'),
        ('short_break_count', 'Short break count before first long break'),
        ('format', 'format string, available formatters: current_pomodoro, '
                   'total_pomodoro, time')
    )
    required = ('sound',)

    color_stopped = '#2ECCFA'
    color_running = '#FFFF00'
    color_break = '#37FF00'
    interval = 1
    short_break_count = 3
    format = '☯ {current_pomodoro}/{total_pomodoro} {time}'

    pomodoro_duration = 25 * 60
    break_duration = 5 * 60
    long_break_duration = 15 * 60

    on_rightclick = "stop"
    on_leftclick = "start"

    def init(self):
        # state could be either running/break or stopped
        self.state = 'stopped'
        self.breaks = 0
        self.time = None

    def run(self):
        if self.time and datetime.now() >= self.time:
            if self.state == 'running':
                self.state = 'break'
                if self.breaks == self.short_break_count:
                    self.time = datetime.now() + \
                        timedelta(seconds=self.long_break_duration)
                    self.breaks = 0
                else:
                    self.time = datetime.now() + \
                        timedelta(seconds=self.break_duration)
                    self.breaks += 1
                text = 'Go for a break!'
            else:
                self.state = 'running'
                self.time = datetime.now() + \
                    timedelta(seconds=self.pomodoro_duration)
                text = 'Back to work!'
            self._alarm(text)

        if self.state == 'running' or self.state == 'break':
            min, sec = divmod((self.time - datetime.now()).total_seconds(), 60)
            text = '{:02}:{:02}'.format(int(min), int(sec))
            color = self.color_running if self.state == 'running' else self.color_break
        else:
            self.output = {
                'full_text': 'Stopped',
                'color': self.color_stopped
            }
            return

        sdict = {
            'time': text,
            'current_pomodoro': self.breaks,
            'total_pomodoro': self.short_break_count + 1,
        }
        self.data = sdict
        self.output = {
            'full_text': self.format.format(**sdict),
            'color': color
        }

    def start(self):
        self.state = 'running'
        self.time = datetime.now() + timedelta(seconds=self.pomodoro_duration)
        self.breaks = 0

    def stop(self):
        self.state = 'stopped'
        self.time = None

    def _alarm(self, text):
        subprocess.call(['notify-send',
                         'Alarm!',
                         text])
        subprocess.Popen(['aplay',
                          self.sound,
                          '-q'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
