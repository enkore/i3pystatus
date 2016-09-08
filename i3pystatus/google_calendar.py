import datetime

import httplib2
import oauth2client
import pytz
from apiclient import discovery
from dateutil import parser
from googleapiclient.errors import HttpError
from i3pystatus import IntervalModule, logger
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.core.util import internet, require, user_open


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
        ("days", "Only show events between now and this many days in the future"),
        ("urgent_seconds", "Add urgent hint when this many seconds until event startTime"),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'"),
    )

    required = ('credential_path',)

    interval = 30

    format = "{summary} ({remaining_time})"
    credential_path = None
    skip_recurring = True
    days = 1
    urgent_seconds = 300
    color = None

    service = None
    credentials = None

    display_event = None

    def on_click(self, button, **kwargs):
        self.open_calendar()

    def init(self):
        self.colors = self.get_hex_color_range(self.end_color, self.start_color, self.urgent_seconds * 2)

    @require(internet)
    def run(self):
        if not self.service:
            self.connect_service()

        try:
            self.display_event = self.get_next_event()
        except ConnectionResetError as e:
            logger.warn(e)

        if self.display_event:
            start_time = self.display_event['start_time']
            now = datetime.datetime.now(tz=pytz.UTC)

            alert_time = now + datetime.timedelta(seconds=self.urgent_seconds)
            self.display_event['remaining_time'] = str((start_time - now)).partition('.')[0]
            urgent = alert_time > start_time
            color = self.get_color(now, start_time)

            self.output = {
                'full_text': self.format.format(**self.display_event),
                'color': color,
                'urgent': urgent
            }
        else:
            self.display_event = None
            self.output = {
                'full_text': "",
            }

    def connect_service(self):
        self.credentials = oauth2client.file.Storage(self.credential_path).get()
        self.service = discovery.build('calendar', 'v3', http=self.credentials.authorize(httplib2.Http()))

    def get_next_event(self):
        for event in self.get_events():
            # If we don't have a dateTime just make do with a date.
            if 'dateTime' not in event['start']:
                event['start_time'] = pytz.utc.localize(parser.parse(event['start']['date']))
            else:
                event['start_time'] = parser.parse(event['start']['dateTime'])

            now = datetime.datetime.now(tz=pytz.UTC)
            if 'recurringEventId' in event and self.skip_recurring:
                continue
            elif event['start_time'] < now:
                continue

            # It is possible for there to be no title...
            if 'summary' not in event:
                event['summary'] = '(no title)'
            return event

    def get_events(self):
        events = []
        try:
            now, later = self.get_timerange()
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

    def get_timerange(self):
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(days=self.days)
        now = now.isoformat() + 'Z'
        later = later.isoformat() + 'Z'
        return now, later

    def get_color(self, now, start_time):
        seconds_to_event = (start_time - now).seconds
        v = self.percentage(seconds_to_event, self.urgent_seconds)
        color = self.get_gradient(v, self.colors)
        return color

    def open_calendar(self):
        if self.display_event:
            calendar_url = self.display_event.get('htmlLink', None)
            if calendar_url:
                user_open(calendar_url)
