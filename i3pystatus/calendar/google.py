import datetime
from datetime import timezone

import httplib2
import oauth2client
import pytz
from apiclient import discovery
from dateutil import parser
from googleapiclient.errors import HttpError
from i3pystatus.calendar import CalendarBackend, CalendarEvent, formatter
from i3pystatus.core.util import user_open, require, internet


class GoogleCalendarEvent(CalendarEvent):
    def __init__(self, google_event):
        self.id = google_event['id']
        self.title = google_event['summary']
        self.start = self._parse_date(google_event['start'])
        self.end = self._parse_date(google_event['end'])
        self.recurring = 'recurringEventId' in google_event
        self._link = google_event['htmlLink']
        self._status = google_event['status']
        self._kind = google_event['kind']

    @formatter
    def htmlLink(self):
        return self._link

    @formatter
    def status(self):
        return self._status

    @formatter
    def kind(self):
        return self._kind

    def _parse_date(self, date_section):
        if 'dateTime' not in date_section:
            result = parser.parse(date_section['date'])
        else:
            result = parser.parse(date_section['dateTime'])
        return result.replace(tzinfo=timezone.utc).astimezone(tz=None)


class Google(CalendarBackend):
    """
    Calendar backend for interacting with Google Calendar.

    Requires the Google Calendar API package - https://developers.google.com/google-apps/calendar/quickstart/python.
    Additionally requires the `colour`, `httplib2`, `oauth2client`, `pytz`, `apiclient` and `dateutil` modules.

    .. rubric:: Available formatters

    * `{kind}` — type of event
    * `{status}` — eg, confirmed
    * `{htmlLink}` — link to the calendar event
    """

    settings = (
        ('credential_path', 'Path to credentials'),
        ('days', 'Only show events between now and this many days in the future'),
    )

    required = ('credential_path',)

    days = 7

    def init(self):
        self.service = None
        self.events = []

    @require(internet)
    def update(self):
        if self.service is None:
            self.connect_service()
        self.refresh_events()

    def on_click(self, event):
        user_open(event.htmlLink())

    def connect_service(self):
        self.logger.debug("Connecting Service..")
        self.credentials = oauth2client.file.Storage(self.credential_path).get()
        self.service = discovery.build('calendar', 'v3', http=self.credentials.authorize(httplib2.Http()))

    def refresh_events(self):
        """
        Retrieve the next N events from Google.
        """
        now = datetime.datetime.now(tz=pytz.UTC)
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
            self.events.clear()
            for event in events_result.get('items', []):
                self.events.append(GoogleCalendarEvent(event))
        except HttpError as e:
            if e.resp.status in (500, 503):
                self.logger.warn("GoogleCalendar received %s while retrieving events" % e.resp.status)
            else:
                raise

    def get_timerange_formatted(self, now):
        """
        Return two ISO8601 formatted date strings, one for timeMin, the other for timeMax (to be consumed by get_events)
        """
        later = now + datetime.timedelta(days=self.days)
        return now.isoformat(), later.isoformat()
