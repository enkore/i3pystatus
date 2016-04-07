from i3pystatus import IntervalModule
import subprocess, re


class Latency(IntervalModule):

    """Print internet connection latency."""

    settings = (
        ('color_good', 'Text color with good latency'),
        ('color_bad', 'Text color with bad latency'),
        ('color_offline', 'Text color when offline'),
        ('latency_threshold', 'Maximum latency to be considered good in ms'),
        ('format', 'Status text format'),
        ('format_offline', 'Status text when offline'),
        ('host', 'Host to ping'),
    )

    color_good = '#ffffff'
    color_bad = '#ffff00'
    color_offline = '#ff0000'
    latency_threshold = 120
    format = '{latency} ms'
    format_offline = 'offline'
    host = '8.8.8.8'
    interval = 10

    def run(self):
        proc = subprocess.run(['ping', '-c1', self.host], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            self.output = {
                'color': self.color_offline,
                'full_text': self.format_offline
            }
            return

        string = proc.stdout.decode('ascii').split('\n')[-2]
        match = re.search('[0-9\.]+', string)
        if match is None:
            self.output = {
                'full_text': 'Unknown error'
            }
            return

        latency = float(match.group(0))
        cdict = {
            'latency': latency
        }

        if latency > self.latency_threshold:
            self.output = {
                'color': self.color_bad,
                'full_text': self.format.format(**cdict)
            }
        else:
            self.output = {
                'color': self.color_good,
                'full_text': self.format.format(**cdict)
            }
