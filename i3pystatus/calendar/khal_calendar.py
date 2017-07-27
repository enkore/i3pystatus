from datetime import date, timedelta

import khal
import khal.cli
import khal.settings
from i3pystatus.calendar import CalendarBackend, CalendarEvent, formatter


class KhalEvent(CalendarEvent):
    def __init__(self, khal_event):
        self.id = khal_event.uid
        self.start = khal_event.start_local
        self.end = khal_event.end_local
        self.title = khal_event.summary
        self.recurring = khal_event.recurring
        self._calendar = khal_event.calendar

    @formatter
    def calendar(self):
        return self._calendar


class Khal(CalendarBackend):
    """
    Backend for Khal. Requires `khal` to be installed.

    .. rubric:: Available formatters
        * `{calendar}` — Calendar event is from.
    """

    settings = (
        ('config_path', 'Path to your khal.conf'),
        ('calendars', 'Restrict to these calendars pass as a list)'),
        ('days', 'Check for the next X days'),
    )

    required = ('config_path', 'calendars')

    days = 7

    config_path = None
    calendars = None

    def init(self):
        self.collection = None
        self.events = []

    def open_connection(self):
        self.logger.debug("Opening collection with config {}".format(self.config_path))
        config = khal.settings.get_config(self.config_path)
        self.collection = khal.cli.build_collection(config, None)

    def update(self):
        if self.collection is None:
            self.open_connection()
        events = []
        for days in range(self.days):
            events += list(self.collection.get_events_on(
                date.today() + timedelta(days=days))
            )

        # filter out unwanted calendars
        self.logger.debug("calendars %s" % self.calendars)
        if self.calendars is not None:
            events = [evt for evt in events if evt.calendar in self.calendars]
        for event in events:
            self.events.append(KhalEvent(event))
