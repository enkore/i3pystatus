import sqlite3
from datetime import datetime

import pytz
from dateutil.tz import tzlocal
from i3pystatus.calendar import CalendarEvent, CalendarBackend, formatter


class Flag:
    PRIVATE = 1
    HAS_ATTENDEES = 2
    HAS_PROPERTIES = 4
    EVENT_ALLDAY = 8
    HAS_RECURRENCE = 16
    HAS_EXCEPTIONS = 32
    HAS_ATTACHMENTS = 64
    HAS_RELATIONS = 128
    HAS_ALARMS = 256
    RECURRENCE_ID_ALLDAY = 512


class LightningCalendarEvent(CalendarEvent):
    def __init__(self, row):
        self.id = row['id']
        self.title = row['title']
        self._event_start = row['event_start']
        self._event_start_tz = row['event_start_tz']
        self._event_end = row['event_end']
        self._event_end_tz = row['event_end_tz']
        self._flags = row['flags']
        self._location = row['location'] or ''

    @property
    def recurring(self):
        return (self._flags & Flag.HAS_RECURRENCE) != 0

    @property
    def end(self):
        return self._convert_date(self._event_end, self._event_end_tz)

    @property
    def start(self):
        return self._convert_date(self._event_start, self._event_start_tz)

    @formatter
    def location(self):
        return self._location

    def _convert_date(self, microseconds_from_epoch, timezone):
        if timezone == 'floating':
            tz = tzlocal()
        else:
            tz = pytz.timezone(timezone)
        d = datetime.fromtimestamp(microseconds_from_epoch / 1000000, tz=pytz.UTC)
        return d.astimezone(tz)


class Lightning(CalendarBackend):
    """
    Backend for querying the Thunderbird's Lightning database. Requires `pytz` and `dateutil`.

    .. rubric:: Available formatters

    * `{location}` — Where the event occurs
    """

    settings = (
        ('database_path', 'Path to local.sqlite.'),
        ('days', 'Only show events between now and this many days in the future'),
    )

    required = ('database_path',)

    days = 7

    database_path = None

    def update(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                  id,
                  title,
                  event_start,
                  event_start_tz,
                  event_end,
                  event_end_tz,
                  flags,
                  cal_properties.value AS location
                FROM cal_events
                  LEFT OUTER JOIN cal_properties ON cal_properties.item_id = id AND cal_properties.key = 'LOCATION'
                WHERE
                  datetime(event_start / 1000000, 'unixepoch', 'localtime') < datetime('now', 'localtime', '+' || :days || ' days')
                  AND
                  datetime(event_start / 1000000, 'unixepoch', 'localtime') > datetime('now', 'localtime')
                ORDER BY event_start ASC
            """, dict(days=self.days))
            self.events.clear()
            for row in cursor:
                self.events.append(LightningCalendarEvent(row))
            cursor.close()
