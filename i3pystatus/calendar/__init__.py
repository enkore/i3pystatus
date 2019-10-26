import inspect
import re
import threading
from abc import abstractmethod
from datetime import datetime, timedelta

from i3pystatus import IntervalModule, formatp, SettingsBase
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.core.desktop import DesktopNotification

humanize_imported = False
try:
    import humanize
    humanize_imported = True
except ImportError:
    pass


def strip_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)


def formatter(func):
    """ Decorator to mark a CalendarEvent method as a formatter. """
    func.formatter = True
    return func


class CalendarEvent:
    """
    Simple class representing an Event. The attributes title, start, end and recurring are required as
    these will be used for the formatters. The id attribute is used to uniquely identify the event.

    If a backend wishes to provide extra formatters to the user, this can be done by adding additional
    methods and decorating them with the @formatter decorator. See the LightningCalendarEvent from the
    lightning module for an example of this.
    """

    # Unique identifier for this event
    id = None

    # The title of this event
    title = None

    # Datetime object representing when this event begins
    start = None

    # Datetime object representing when this event ends
    end = None

    # Whether or not this event is a recurring event
    recurring = False

    def formatters(self):
        """
        Build a dictionary containing all those key/value pairs that will be exposed to the user via formatters.
        """
        event_dict = dict(
            title=self.title,
            remaining=self.time_remaining,
            humanize_remaining=self.humanize_time_remaining,
        )

        def is_formatter(x):
            return inspect.ismethod(x) and hasattr(x, 'formatter') and getattr(x, 'formatter')

        for method_name, method in inspect.getmembers(self, is_formatter):
            event_dict[method_name] = method()
        return event_dict

    @property
    def time_remaining(self):
        return strip_microseconds(self.start - datetime.now(tz=self.start.tzinfo))

    @property
    def humanize_time_remaining(self):
        if humanize_imported:
            return humanize.naturaltime(datetime.now(tz=self.start.tzinfo) - self.start)

    def __str__(self):
        return "{}(title='{}', start={}, end={}, recurring={})" \
            .format(type(self).__name__,
                    self.title,
                    repr(self.start),
                    repr(self.end),
                    self.recurring)


class CalendarBackend(SettingsBase):
    """
    Base class for calendar backend. Subclasses should implement update and populate the events list.

    Optionally, subclasses can override on_click to perform actions on the current event when clicked.
    """

    def init(self):
        self.events = []

    @abstractmethod
    def update(self):
        """ Subclasses should implement this method and populate the events list with CalendarEvents."""

    def on_click(self, event):
        """ Override this method to do more interesting things with the event. """
        DesktopNotification(
            title=event.title,
            body="{} until {}!".format(event.time_remaining, event.title),
            icon='dialog-information',
            urgency=1,
            timeout=0,
        ).display()

    def __iter__(self):
        return iter(self.events)

    def __len__(self):
        return len(self.events)


class Calendar(IntervalModule, ColorRangeModule):
    """
    Generic calendar module. Requires the PyPI package ``colour``.

    .. rubric:: Available formatters

    * {title} - the title or summary of the event
    * {remaining_time} - how long until this event is due
    * {humanize_remaining} - how long until this event is due in human readable format

    Additional formatters may be provided by the backend, consult their documentation for details.

    .. note:: Optionally requires `humanize` to display time in human readable format.
    """

    settings = (
        ('format', 'Format string to display in the bar'),
        ('backend', 'Backend to use for collecting calendar events'),
        ('skip_recurring', 'Whether or not to skip recurring events'),
        ('skip_all_day', 'Whether or not to skip all day events'),
        ('skip_regex', 'Skip events with titles that match this regex'),
        ('update_interval', "How often in seconds to call the backend's update method"),
        ('urgent_seconds', "When within this many seconds of the event, set the urgent flag"),
        ('urgent_blink', 'Whether or not to blink when within urgent_seconds of the event'),
        ('dynamic_color', 'Whether or not to change color as the event approaches'),
        'color'
    )

    required = ('backend',)

    skip_recurring = False
    skip_all_day = False
    skip_regex = None
    interval = 1
    backend = None
    update_interval = 600
    dynamic_color = True
    urgent_seconds = 300
    urgent_blink = False
    color = None

    current_event = None
    urgent_acknowledged = False

    format = "{title} - {remaining}"

    on_rightclick = 'handle_click'
    on_leftclick = 'acknowledge'

    def init(self):
        if 'humanize_remaining' in self.format and not humanize_imported:
            raise ImportError('Missing humanize module')

        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.update_thread, daemon=True)
        self.thread.start()
        self.colors = self.get_hex_color_range(self.end_color, self.start_color, self.urgent_seconds * 2)

    def update_thread(self):
        self.refresh_events()
        while True:
            with self.condition:
                self.condition.wait(self.update_interval)
            self.refresh_events()

    def refresh_events(self):
        self.backend.update()

        def valid_event(ev):
            if self.skip_all_day and not isinstance(ev.start, datetime):
                return False
            if self.skip_recurring and ev.recurring:
                return False
            if self.skip_regex and re.search(self.skip_regex, ev.title) is not None:
                return False
            elif ev.time_remaining < timedelta(seconds=0):
                return False
            return True

        for event in self.backend:
            if valid_event(event):
                if self.current_event and self.current_event.id != event.id:
                    self.urgent_acknowledged = False
                self.current_event = event
                return
        self.current_event = None

    def run(self):
        if self.current_event and self.current_event.time_remaining > timedelta(seconds=0):
            color = None
            if self.color is not None:
                color = self.color
            elif self.dynamic_color:
                color = self.get_color()
            self.output = {
                "full_text": formatp(self.format, **self.current_event.formatters()),
                "color": color,
                "urgent": self.is_urgent()
            }
        else:
            self.output = {}

    def handle_click(self):
        if self.current_event:
            self.backend.on_click(self.current_event)

    def get_color(self):
        if self.current_event.time_remaining.days > 0:
            color = self.colors[-1]
        else:
            p = self.percentage(self.current_event.time_remaining.seconds, self.urgent_seconds)
            color = self.get_gradient(p, self.colors)
        return color

    def is_urgent(self):
        """
        Determine whether or not to set the urgent flag. If urgent_blink is set, toggles urgent flag
        on and off every second.
        """
        if not self.current_event:
            return False
        now = datetime.now(tz=self.current_event.start.tzinfo)
        alert_time = now + timedelta(seconds=self.urgent_seconds)
        urgent = alert_time > self.current_event.start
        if urgent and self.urgent_blink:
            urgent = now.second % 2 == 0 and not self.urgent_acknowledged
        return urgent

    def acknowledge(self):
        self.urgent_acknowledged = not self.urgent_acknowledged
