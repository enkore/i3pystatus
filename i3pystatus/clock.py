import errno
import os
import locale
from datetime import datetime

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

from i3pystatus import IntervalModule


class Clock(IntervalModule):
    """
    This class shows a clock.

    .. note:: Optionally requires `pytz` for time zone data when using time
        zones other than local time.

    Format can be passed in four different ways:

    - single string, no timezone, just the strftime-format
    - one two-tuple, first is the format, second the timezone
    - list of strings - no timezones
    - list of two tuples, first is the format, second is timezone

    Use mousewheel to cycle between formats.

    For complete time format specification see:

    ::

        man strftime

    All available timezones are located in directory:

    ::

        /usr/share/zoneinfo/

    .. rubric:: Format examples

    ::

        # one format, local timezone
        format = '%a %b %-d %b %X'
        # multiple formats, local timezone
        format = [ '%a %b %-d %b %X', '%X' ]
        # one format, specified timezone
        format = ('%a %b %-d %b %X', 'Europe/Bratislava')
        # multiple formats, specified timezones
        format = [ ('%a %b %-d %b %X', 'America/New_York'), ('%X', 'Etc/GMT+9') ]

    """

    settings = (
        ("format", "`None` means to use the default, locale-dependent format."),
        ("color", "RGB hexadecimal code color specifier, default to #ffffff"),
    )
    format = None
    color = "#ffffff"
    interval = 1
    on_upscroll = ["scroll_format", 1]
    on_downscroll = ["scroll_format", -1]

    def init(self):
        env_lang = os.environ.get('LC_TIME', None)
        if env_lang is None:
            env_lang = os.environ.get('LANG', None)

        if env_lang is not None:
            if env_lang.find('.') != -1:
                lang = tuple(env_lang.split('.', 1))
            else:
                lang = (env_lang, None)
        else:
            lang = (None, None)

        if lang != locale.getlocale(locale.LC_TIME):
            # affects language of *.strftime() in whole program
            locale.setlocale(locale.LC_TIME, lang)

        if self.format is None:
            if lang[0] == 'en_US':
                # MDY format - United States of America
                self.format = ["%a %b %-d %X"]
            else:
                # DMY format - almost all other countries
                self.format = ["%a %-d %b %X"]

        elif isinstance(self.format, str) or isinstance(self.format, tuple):
            self.format = [self.format]

        self.system_tz = self._get_system_tz()
        self.format = [self._expand_format(fmt) for fmt in self.format]
        self.current_format_id = 0

    def _expand_format(self, fmt):
        if isinstance(fmt, tuple):
            if len(fmt) == 1:
                return (fmt[0], None)
            else:
                if not HAS_PYTZ:
                    raise RuntimeError("Need `pytz` for timezone data")
                return (fmt[0], pytz.timezone(fmt[1]))
        return (fmt, self.system_tz)

    def _get_system_tz(self):
        '''
        Get the system timezone for use when no timezone is explicitly provided

        Requires pytz, if not available then no timezone will be set when not
        explicitly provided.
        '''
        if not HAS_PYTZ:
            return None

        def _etc_localtime():
            try:
                with open('/etc/localtime', 'rb') as fp:
                    return pytz.tzfile.build_tzinfo('system', fp)
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    self.logger.error(
                        'Unable to read from /etc/localtime: %s', exc.strerror
                    )
            except pytz.UnknownTimeZoneError:
                self.logger.error(
                    '/etc/localtime contains unrecognized tzinfo'
                )
            return None

        def _etc_timezone():
            try:
                with open('/etc/timezone', 'r') as fp:
                    tzname = fp.read().strip()
                return pytz.timezone(tzname)
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    self.logger.error(
                        'Unable to read from /etc/localtime: %s', exc.strerror
                    )
            except pytz.UnknownTimeZoneError:
                self.logger.error(
                    '/etc/timezone contains unrecognized timezone \'%s\'',
                    tzname
                )
            return None

        return _etc_localtime() or _etc_timezone()

    def run(self):
        time = datetime.now(self.format[self.current_format_id][1])

        self.output = {
            "full_text": time.strftime(self.format[self.current_format_id][0]),
            "color": self.color,
            "urgent": False,
        }

    def scroll_format(self, step=1):
        self.current_format_id = (self.current_format_id + step) % len(self.format)
