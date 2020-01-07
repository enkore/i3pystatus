from i3pystatus import IntervalModule
from json import loads
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone
import subprocess


class Timewarrior(IntervalModule):
    """
    Show current Timewarrior tracking
    Requires `json` `dateutil`

    Formaters:

    * `{tags}`  — contains tags of current track
    * `{start}` - contains start of track
    * `{duration}` — contains time of current track
    """

    format = '{duration}'
    duration_format = '{years}y{months}m{days}d{hours}h{minutes}m{seconds}s'
    enable_stop = True
    enable_continue = True
    color_running = '#00FF00'
    color_stopped = '#F00000'
    on_rightclick = 'stop_or_continue'
    track = None

    settings = (
        ('format', 'format string'),
        ('duration_format', 'duration format string'),
        ('enable_stop', 'Allow right click to stop tracking'),
        ('enable_continue', 'ALlow right click to continue tracking'),
        ('color_running', '#00FF00'),
        ('color_stopped', '#F00000'),
    )

    def loadTrack(self):
        try:
            tracks_json = subprocess.check_output(['timew', 'export'])
            tracks = loads(tracks_json.decode("utf-8"))
            self.track = tracks[-1]

        except ValueError as error:
            self.logger.exception('Decoding JSON has failed')
            raise error

    def stop_or_continue(self):
        self.loadTrack()

        if 'end' in self.track and self.enable_continue:
            subprocess.check_output(['timew', 'continue'])
        elif self.enable_stop:
            subprocess.check_output(['timew', 'stop'])

    def run(self):
        self.loadTrack()
        start = parse(self.track['start'])
        end = parse(self.track['end']) if 'end' in self.track else datetime.now(timezone.utc)
        duration = relativedelta(end, start)

        format_values = dict(
            tags=", ".join(self.track['tags'] if 'tags' in self.track else []),
            start=start,
            duration=self.duration_format.format(
                years=duration.years,
                months=duration.months,
                days=duration.days,
                hours=duration.hours,
                minutes=duration.minutes,
                seconds=duration.seconds,
            )
        )

        self.output = {
            'full_text': self.format.format(**format_values),
            'color': self.color_stopped if 'end' in self.track else self.color_running
        }
