
from i3pystatus import IntervalModule
from i3pystatus import logger
from i3pystatus.core import ConfigError
from i3pystatus.core.util import user_open, internet, require
import khal
import khal.settings
import khal.cli
from datetime import datetime, date, timedelta


class KhalCalendar(IntervalModule):
    """

    .. rubric:: Available formatters

    * `{calendars}`        —  Current calendar
    * `{nb_events}`  — number of events for the day
    * `{next_event}`  —  Display next event summary
    """

    color = '#78EAF2'
    format = '{nb_events} event(s) {next_event}'
    interval = 1

    current_calendar = None
    config_filename = None
    on_rightclick = 'termite -e ikhal'

    calendars = None
    days = 1

    settings = (
        ('config_filename', "Path to your khal.conf"),
        ('format', 'Format string'),
        ("calendars", "Restrict to these calendars pass as a list) "),
        ("days", "Check for the next X days"),
    )

    def init(self):
        self.config = khal.settings.get_config(self.config_filename)
        self.collection = None

    def open_connection(self,):
        self.logger.debug("Opening collection")
        self.collection = khal.cli.build_collection(self.config, None,)
        self.logger.debug("Available calendars=%s" % self.collection.names)

    def run(self):

        format_values = dict(calendar='', next_event='', nb_events=0)

        if self.collection is None:
            self.open_connection()

        self.logger.info("Running")

        # retrieve events for the next X days
        events = []
        for days in range(self.days):
            events += list(self.collection.get_events_on(
                date.today() + timedelta(days=days))
            )

        # filter out unwanted calendars
        self.logger.debug("calendars %s" % self.calendars)
        if self.calendars is not None:
            events = [evt for evt in events if evt.calendar in self.calendars]

        if len(events):
            # We could probably add an option see
            # http://khal.readthedocs.io/en/latest/usage.html#cmdoption--format
            format_values['next_event'] = events[0].summary

        format_values['nb_events'] = len(events)

        self.data = format_values
        self.output = {
            'full_text': self.format.format(**format_values),
            'color': self.color
        }
