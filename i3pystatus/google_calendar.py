import datetime
import threading

import httplib2
import oauth2client
import pytz
from apiclient import discovery
from dateutil import parser
from googleapiclient.errors import HttpError

from i3pystatus import IntervalModule, logger
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.core.util import user_open, internet, require


class GoogleCalendar(IntervalModule, ColorRangeModule):
    """
    Simple module for displaying next Google Calendar event.

    Requires the Google Calendar API package - https://developers.google.com/google-apps/calendar/quickstart/python.
    Additionally requires the `colour`, `httplib2`, `oauth2client`, `pytz`, `apiclient` and `dateutil` modules.

    All top level keys returned by the Google Calendar API can be used as formatters. Some
    examples include:

    .. rubric:: Available formatters

    * `{kind}` — type of event
    * `{status}` — eg, confirmed
    * `{summary}` — essentially the title
    * `{remaining_time}` - how long remaining until the event
    * `{start_time}` - when this event starts
    * `{htmlLink}` — link to the calendar event


    """
    settings = (
        ('format', 'format string'),
        ("credential_path", "Path to credentials"),
        ("skip_recurring", "Skip recurring events."),
        ("update_interval", "How often (in seconds) to call the Goggle API and update events"),
        ("days", "Only show events between now and this many days in the future"),
        ("urgent_seconds", "Add urgent hint when this many seconds until event startTime"),
        ("urgent_blink", "Whether or not to blink when the within urgent_seconds of event start"),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'"),
    )

    required = ('credential_path',)

    format = "{summary} ({remaining_time})"
    credential_path = None
    interval = 1

    skip_recurring = True
    update_interval = 60
    days = 1
    urgent_seconds = 300
    urgent_blink = False
    color = None

    service = None
    credentials = None

    display_event = None
    last_event_refresh = None
    urgent_acknowledged = False
    update_lock = threading.Lock()

    on_rightclick = 'acknowledge'
    on_leftclick = 'open_calendar'

    def init(self):
        self.colors = self.get_hex_color_range(self.end_color, self.start_color, self.urgent_seconds * 2)
        self.last_event_refresh = datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(seconds=self.update_interval)
        self.connect_service()

    @require(internet)
    def run(self):
        now = datetime.datetime.now(tz=pytz.UTC)
        if self.should_update(now):
            threading.Thread(target=self.update_display_event, args=(now,), daemon=True).start()
        self.refresh_output(now)

    def should_update(self, now):
        """
        Whether or not we should update events.
        """
        wait_window = self.last_event_refresh + datetime.timedelta(seconds=self.update_interval)
        if self.display_event is None:
            should_update = wait_window < now
        elif self.display_event['start_time'] < now:
            should_update = True
        elif wait_window < now:
            should_update = True
        else:
            should_update = False
        return should_update and not self.update_lock.locked()

    def update_display_event(self, now):
        """
        Call the Google API and attempt to update the current event.
        """
        with self.update_lock:
            logger.debug("Retrieving events...".format(threading.current_thread().name))
            self.last_event_refresh = now
            for event in self.get_events(now):
                # If we don't have a dateTime just make do with a date.
                if 'dateTime' not in event['start']:
                    event['start_time'] = pytz.utc.localize(parser.parse(event['start']['date']))
                else:
                    event['start_time'] = parser.parse(event['start']['dateTime'])

                if 'recurringEventId' in event and self.skip_recurring:
                    continue
                elif event['start_time'] < now:
                    continue

                # It is possible for there to be no title...
                if 'summary' not in event:
                    event['summary'] = '(no title)'

                if self.display_event:
                    # If this is a new event, reset the urgent_acknowledged flag.
                    if self.display_event['id'] != event['id']:
                        self.urgent_acknowledged = False
                self.display_event = event
                return
        self.display_event = None

    def refresh_output(self, now):
        """
        Build our output dict.
        """
        if self.display_event:
            start_time = self.display_event['start_time']
            alert_time = now + datetime.timedelta(seconds=self.urgent_seconds)
            self.display_event['remaining_time'] = str((start_time - now)).partition('.')[0]
            urgent = self.is_urgent(alert_time, start_time, now)
            color = self.get_color(now, start_time)

            self.output = {
                'full_text': self.format.format(**self.display_event),
                'color': color,
                'urgent': urgent
            }
        else:
            self.output = {
                'full_text': "",
            }

    def is_urgent(self, alert_time, start_time, now):
        """
        Determine whether or not to set the urgent flag. If urgent_blink is set, toggles urgent flag
        on and off every second.
        """
        urgent = alert_time > start_time
        if urgent and self.urgent_blink:
            urgent = now.second % 2 == 0 and not self.urgent_acknowledged
        return urgent

    def get_events(self, now):
        """
        Retrieve the next N events from Google.
        """
        events = []
        try:
            now, later = self.get_timerange_formatted(now)
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=later,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime',
                timeZone='utc'
            ).execute()
            events = events_result.get('items', [])
        except HttpError as e:
            if e.resp.status in (500, 503):
                logger.warn("GoogleCalendar received %s while retrieving events" % e.resp.status)
            else:
                raise
        return events

    def get_timerange_formatted(self, now):
        """
        Return two ISO8601 formatted date strings, one for timeMin, the other for timeMax (to be consumed by get_events)
        """
        later = now + datetime.timedelta(days=self.days)
        return now.isoformat(), later.isoformat()

    def get_color(self, now, start_time):
        seconds_to_event = (start_time - now).seconds
        v = self.percentage(seconds_to_event, self.urgent_seconds)
        color = self.get_gradient(v, self.colors)
        return color

    def connect_service(self):
        logger.debug("Connecting Service..")
        self.credentials = oauth2client.file.Storage(self.credential_path).get()
        self.service = discovery.build('calendar', 'v3', http=self.credentials.authorize(httplib2.Http()))

    def open_calendar(self):
        if self.display_event:
            calendar_url = self.display_event.get('htmlLink', None)
            if calendar_url:
                user_open(calendar_url)

    def acknowledge(self):
        self.urgent_acknowledged = True
