
from i3pystatus import IntervalModule
from i3pystatus import logger
from i3pystatus.core import ConfigError
from i3pystatus.core.util import user_open, internet, require
import khal
import khal.settings
import khal.cli
from  datetime import datetime, date




class KhalCalendar(IntervalModule):
    """

    .. rubric:: Available formatters

    * `{calendar}`        —  Current calendar
    * `{nb_events}`  — number of events for the day

        See http://khal.readthedocs.io/en/latest/usage.html#cmdoption--format
    """

    max_error_len = 50
    color = '#78EAF2'
    format = '{calendar} / {nb_events}'
    interval = 1

    current_calendar = None
    config_filename = None
    on_rightclick = 'termite -e ikhal'

    on_upscroll = ["cycle_through_calendars", 1]
    on_downscroll = ["cycle_through_calendars", -1]

    settings = (
        ('config_filename', "Path to your khal.conf"),
        ('format', 'Format string'),
        ("calendar", "calendar name"),
        ("next_event", "see https://developer.github.com/v3/#authentication"),
        ("nb_events", "Number of events within the selection")
    )

    def init(self):
        self.config = khal.settings.get_config(self.config_filename)
        self.collection = None
        self.current_calendar = None

        # CalendarCollection is defined in khalendar.py
    def cycle_through_calendars(self, step=1):
        # from itertools import cycle


        # print(self.config["calendars"])
        self.logger.info("hello world %s" % self.config["calendars"])
        try:
            calendars = self.config["calendars"].keys()
            idx = calendars.index(self.current_calendar)
            self.current_calendar  = calendars[ idx + step % len(calendars) ]
            self.logger.info("Newly selected calender %s" % self.current_calendar)
        except ValueError:
            self.current_calendar = self.collection.default_calendar_name


    def open_connection(self,):
        self.logger.debug("Opening collection")
        self.collection = khal.cli.build_collection(self.config, None,) 
        self.current_calendar = self.collection.default_calendar_name

    def run(self):

        format_values = dict(calendar='', next_event='', nb_events=0)

        if self.collection is None:
            self.open_connection()

        self.logger.info("Running")
        format_values['calendar'] = self.current_calendar
        events = list(self.collection.get_events_on( date.today() ))

        if len(events):
            format_values['next_event'] = events[0].summary

        format_values['nb_events'] = len(events)

        self.data = format_values
        self.output = {
            'full_text': self.format.format(**format_values),
            'color': self.color
        }
