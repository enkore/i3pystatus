import subprocess
from datetime import datetime, timedelta
from i3pystatus import IntervalModule
from i3pystatus.core.desktop import DesktopNotification


STOPPED = 0
RUNNING = 1
BREAK = 2


class Pomodoro(IntervalModule):

    """
    This plugin shows Pomodoro timer.

    Left click starts/restarts timer.
    Right click stops it.

    Example color settings.

    .. code-block:: python

        color_map = {
            'stopped': '#2ECCFA',
            'running': '#FFFF00',
            'break': '#37FF00'
        }
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
                   'total_pomodoro, time'),
        ('inactive_format', 'format string to display when no timer is running'),
        ('color', 'dictionary containing a mapping of statuses to colours')
    )

    inactive_format = 'Start Pomodoro'

    color_map = {
        'stopped': '#2ECCFA',
        'running': '#FFFF00',
        'break': '#37FF00'
    }

    color = None
    sound = None

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
        self.state = STOPPED
        self.current_pomodoro = 0
        self.total_pomodoro = self.short_break_count + 1  # and 1 long break
        self.time = None

        if self.color is not None and type(self.color) == dict:
            self.color_map.update(self.color)

    def run(self):
        if self.time and datetime.utcnow() >= self.time:
            if self.state == RUNNING:
                self.state = BREAK
                if self.current_pomodoro == self.short_break_count:
                    self.time = datetime.utcnow() + \
                        timedelta(seconds=self.long_break_duration)
                else:
                    self.time = datetime.utcnow() + \
                        timedelta(seconds=self.break_duration)
                text = 'Go for a break!'
            else:
                self.state = RUNNING
                self.time = datetime.utcnow() + \
                    timedelta(seconds=self.pomodoro_duration)
                text = 'Back to work!'
                self.current_pomodoro = (self.current_pomodoro + 1) % self.total_pomodoro
            self._alarm(text)

        if self.state == RUNNING or self.state == BREAK:
            min, sec = divmod((self.time - datetime.utcnow()).total_seconds(), 60)
            text = '{:02}:{:02}'.format(int(min), int(sec))
            sdict = {
                'time': text,
                'current_pomodoro': self.current_pomodoro + 1,
                'total_pomodoro': self.total_pomodoro
            }

            color = self.color_map['running'] if self.state == RUNNING else self.color_map['break']
            text = self.format.format(**sdict)
        else:
            text = self.inactive_format
            color = self.color_map['stopped']

        self.output = {
            'full_text': text,
            'color': color
        }

    def start(self):
        self.state = RUNNING
        self.time = datetime.utcnow() + timedelta(seconds=self.pomodoro_duration)
        self.current_pomodoro = 0

    def stop(self):
        self.state = STOPPED
        self.time = None

    def _alarm(self, text):
        notification = DesktopNotification(title='Alarm!', body=text)
        notification.display()

        if self.sound is not None:
            subprocess.Popen(['aplay',
                              self.sound,
                              '-q'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
