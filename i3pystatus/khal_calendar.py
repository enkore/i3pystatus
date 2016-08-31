
from i3pystatus import IntervalModule
from i3pystatus import logger
from i3pystatus.core import ConfigError
from i3pystatus.core.util import user_open, internet, require
import khal
import khal.settings
import khal.cli
from  datetime import datetime, date




class Calendar(IntervalModule):
    """
    Check events for pending events
    Eventually we should support all theses
 http://khal.readthedocs.io/en/latest/usage.html#cmdoption--format
event.format('{start-date} {summary}')


    Requires `requests`

    Availables authentication methods:

    * username + password
    * access_token (manually generate a new token at https://github.com/settings/tokens)

    See https://developer.github.com/v3/#authentication for more informations.

    Formatters:

    * `{unread}`        — contains the value of unread_marker when there are pending notifications
    * `{unread_count}`  — number of unread notifications, empty if 0
    """

    max_error_len = 50
    next_event = ""
    nb_events = ""
    format_event = '{start-date} {summary}'
    color = '#78EAF2'
    username = ''
    password = ''
    access_token = ''
    format = '{name} / {nb_events}'
    interval = 600
    keyring_backend = None

    on_leftclick = ''

    settings = (
        ('format', 'format string'),
        ('format_event', 'See http://khal.readthedocs.io/en/latest/usage.html#cmdoption--format'),
        ("name", "calendar name"),
        ("next_event", "see https://developer.github.com/v3/#authentication"),
        ("nb_events", "")
    )

    def init(self):
        self.config = khal.settings.get_config()
        self.collection = khal.cli.build_collection(self.config, None)

        # CalendarCollection is defined in khalendar.py
        # u can its use in khalendar_test.py

    def run(self):

        format_values = dict(name='', next_event='', nb_events='')

        # print(self.collection)
        format_values['name'] = self.collection.default_calendar_name
        events = list(self.collection.get_events_on( date.today() ))
        # of type event.py
        if len(events):
            format_values['next_event'] = events[0].summary

        format_values['nb_events'] = len(events)

        self.data = format_values
        self.output = {
            'full_text': self.format.format(**format_values),
            'color': self.color
        }
