import json
import re
import threading
import time
from urllib.request import urlopen

from i3pystatus import SettingsBase, IntervalModule, formatp
from i3pystatus.core.util import user_open, internet, require


class WeatherBackend(SettingsBase):
    settings = ()

    @require(internet)
    def api_request(self, url):
        self.logger.debug('Making API request to %s', url)
        try:
            with urlopen(url) as content:
                try:
                    content_type = dict(content.getheaders())['Content-Type']
                    charset = re.search(r'charset=(.*)', content_type).group(1)
                except AttributeError:
                    charset = 'utf-8'
                response_json = content.read().decode(charset).strip()
                if not response_json:
                    self.logger.debug('JSON response from %s was blank', url)
                    return {}
                try:
                    response = json.loads(response_json)
                except json.decoder.JSONDecodeError as exc:
                    self.logger.error('Error loading JSON: %s', exc)
                    self.logger.debug('JSON text that failed to load: %s',
                                      response_json)
                    return {}
                self.logger.log(5, 'API response: %s', response)
                error = self.check_response(response)
                if error:
                    self.logger.error('Error in JSON response: %s', error)
                    return {}
                return response
        except Exception as exc:
            self.logger.error(
                'Failed to make API request to %s. Exception follows:', url,
                exc_info=True
            )
            return {}

    def check_response(response):
        raise NotImplementedError


class Weather(IntervalModule):
    '''
    This is a generic weather-checker which must use a configured weather
    backend. For list of all available backends see :ref:`weatherbackends`.

    Double-clicking on the module will launch the forecast page for the
    location being checked, and single-clicking will trigger an update.

    .. _weather-formatters:

    .. rubric:: Available formatters

    * `{city}` — Location of weather observation
    * `{condition}` — Current weather condition (Rain, Snow, Overcast, etc.)
    * `{icon}` — Icon representing the current weather condition
    * `{observation_time}` — Time of weather observation (supports strftime format flags)
    * `{current_temp}` — Current temperature, excluding unit
    * `{low_temp}` — Forecasted low temperature, excluding unit
    * `{high_temp}` — Forecasted high temperature, excluding unit (may be
      empty in the late afternoon)
    * `{temp_unit}` — Either ``°C`` or ``°F``, depending on whether metric or
    * `{feelslike}` — "Feels Like" temperature, excluding unit
    * `{dewpoint}` — Dewpoint temperature, excluding unit
      imperial units are being used
    * `{wind_speed}` — Wind speed, excluding unit
    * `{wind_unit}` — Either ``kph`` or ``mph``, depending on whether metric or
      imperial units are being used
    * `{wind_direction}` — Wind direction
    * `{wind_gust}` — Speed of wind gusts in mph/kph, excluding unit
    * `{pressure}` — Barometric pressure, excluding unit
    * `{pressure_unit}` — ``mb`` or ``in``, depending on whether metric or
      imperial units are being used
    * `{pressure_trend}` — ``+`` if rising, ``-`` if falling, or an empty
      string if the pressure is steady (neither rising nor falling)
    * `{visibility}` — Visibility distance, excluding unit
    * `{visibility_unit}` — Either ``km`` or ``mi``, depending on whether
      metric or imperial units are being used
    * `{humidity}` — Current humidity, excluding percentage symbol
    * `{uv_index}` — UV Index
    * `{update_error}` — When the configured weather backend encounters an
      error during an update, this formatter will be set to the value of the
      backend's **update_error** config value. Otherwise, this formatter will
      be an empty string.

    This module supports the :ref:`formatp <formatp>` extended string format
    syntax. This allows for values to be hidden when they evaluate as False.
    The default **format** string value for this module makes use of this
    syntax to conditionally show the value of the **update_error** config value
    when the backend encounters an error during an update.

    The extended string format syntax also comes in handy for the
    :py:mod:`weathercom <.weather.weathercom>` backend, which at a certain
    point in the afternoon will have a blank ``{high_temp}`` value. Using the
    following snippet in your format string will only display the high
    temperature information if it is not blank:

    ::

        {current_temp}{temp_unit}[ Hi: {high_temp}] Lo: {low_temp}[ {update_error}]

    Brackets are evaluated from the outside-in, so the fact that the only
    formatter in the outer block (``{high_temp}``) is empty would keep the
    inner block from being evaluated at all, and entire block would not be
    displayed.

    See the following links for usage examples for the available weather
    backends:

    - :ref:`Weather.com <weather-usage-weathercom>`
    - :ref:`Weather Underground <weather-usage-wunderground>`

    .. rubric:: Troubleshooting

    If an error is encountered while updating, the ``{update_error}`` formatter
    will be set, and (provided it is in your ``format`` string) will show up
    next to the forecast to alert you to the error. The error message will (by
    default be logged to ``~/.i3pystatus-<pid>`` where ``<pid>`` is the PID of
    the update thread. However, it may be more convenient to manually set the
    logfile to make the location of the log data predictable and avoid clutter
    in your home directory. Additionally, using the ``DEBUG`` log level can
    be helpful in revealing why the module is not working as expected. For
    example:

    .. code-block:: python

        import logging
        from i3pystatus import Status
        from i3pystatus.weather import weathercom

        status = Status(logfile='/home/username/var/i3pystatus.log')

        status.register(
            'weather',
            format='{condition} {current_temp}{temp_unit}[ {icon}][ Hi: {high_temp}][ Lo: {low_temp}][ {update_error}]',
            colorize=True,
            hints={'markup': 'pango'},
            update_error='<span color="#ff0000">!</span>',
            log_level=logging.DEBUG,
            backend=weathercom.Weathercom(
                location_code='94107:4:US',
                units='imperial',
                log_level=logging.DEBUG,
            ),
        )

    .. note::
        The log level must be set separately in both the module and backend
        contexts.
    '''

    settings = (
        ('colorize', 'Vary the color depending on the current conditions.'),
        ('color_icons', 'Dictionary mapping weather conditions to tuples '
                        'containing a UTF-8 code for the icon, and the color '
                        'to be used.'),
        ('color', 'Display color (or fallback color if ``colorize`` is True). '
                  'If not specified, falls back to default i3bar color.'),
        ('backend', 'Weather backend instance'),
        ('refresh_icon', 'Text to display (in addition to any text currently '
                         'shown by the module) when refreshing weather data. '
                         '**NOTE:** Depending on how quickly the update is '
                         'performed, the icon may not be displayed.'),
        ('online_interval', 'seconds between updates when online (defaults to interval)'),
        ('offline_interval', 'seconds between updates when offline (default: 300)'),
        'format',
    )
    required = ('backend',)

    colorize = False
    color_icons = {
        'Fair': (u'\u263c', '#ffcc00'),
        'Fog': (u'', '#949494'),
        'Cloudy': (u'\u2601', '#f8f8ff'),
        'Partly Cloudy': (u'\u2601', '#f8f8ff'),  # \u26c5 is not in many fonts
        'Rainy': (u'\u26c8', '#cbd2c0'),
        'Thunderstorm': (u'\u26a1', '#cbd2c0'),
        'Sunny': (u'\u2600', '#ffff00'),
        'Snow': (u'\u2603', '#ffffff'),
        'default': ('', None),
    }

    color = None
    backend = None
    interval = 1800
    offline_interval = 300
    online_interval = None
    refresh_icon = '⟳'
    format = '{current_temp}{temp_unit}[ {update_error}]'

    output = {'full_text': ''}

    on_doubleleftclick = ['launch_web']
    on_leftclick = ['check_weather']

    def launch_web(self):
        if self.backend.forecast_url and self.backend.forecast_url != 'N/A':
            self.logger.debug('Launching %s in browser', self.backend.forecast_url)
            user_open(self.backend.forecast_url)

    def init(self):
        if self.online_interval is None:
            self.online_interval = int(self.interval)

        if self.backend is None:
            raise RuntimeError('A backend is required')

        self.backend.data = {
            'city': '',
            'condition': '',
            'observation_time': '',
            'current_temp': '',
            'low_temp': '',
            'high_temp': '',
            'temp_unit': '',
            'feelslike': '',
            'dewpoint': '',
            'wind_speed': '',
            'wind_unit': '',
            'wind_direction': '',
            'wind_gust': '',
            'pressure': '',
            'pressure_unit': '',
            'pressure_trend': '',
            'visibility': '',
            'visibility_unit': '',
            'humidity': '',
            'uv_index': '',
            'update_error': '',
        }

        self.backend.init()

        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.update_thread, daemon=True)
        self.thread.start()

    def update_thread(self):
        if internet():
            self.interval = self.online_interval
        else:
            self.interval = self.offline_interval
        try:
            self.check_weather()
            while True:
                with self.condition:
                    self.condition.wait(self.interval)
                self.check_weather()
        except Exception:
            msg = 'Exception in {thread} at {time}, module {name}'.format(
                thread=threading.current_thread().name,
                time=time.strftime('%c'),
                name=self.__class__.__name__,
            )
            self.logger.error(msg, exc_info=True)

    def check_weather(self):
        '''
        Check the weather using the configured backend
        '''
        self.output['full_text'] = \
            self.refresh_icon + self.output.get('full_text', '')
        self.backend.check_weather()
        self.refresh_display()

    def get_color_data(self, condition):
        '''
        Disambiguate similarly-named weather conditions, and return the icon
        and color that match.
        '''
        if condition not in self.color_icons:
            # Check for similarly-named conditions if no exact match found
            condition_lc = condition.lower()
            if 'cloudy' in condition_lc or 'clouds' in condition_lc:
                if 'partly' in condition_lc:
                    condition = 'Partly Cloudy'
                else:
                    condition = 'Cloudy'
            elif condition_lc == 'overcast':
                condition = 'Cloudy'
            elif 'thunder' in condition_lc or 't-storm' in condition_lc:
                condition = 'Thunderstorm'
            elif 'snow' in condition_lc:
                condition = 'Snow'
            elif 'rain' in condition_lc or 'showers' in condition_lc:
                condition = 'Rainy'
            elif 'sunny' in condition_lc:
                condition = 'Sunny'
            elif 'clear' in condition_lc or 'fair' in condition_lc:
                condition = 'Fair'
            elif 'fog' in condition_lc:
                condition = 'Fog'

        return self.color_icons['default'] \
            if condition not in self.color_icons \
            else self.color_icons[condition]

    def refresh_display(self):
        self.logger.debug('Weather data: %s', self.backend.data)
        self.backend.data['icon'], condition_color = \
            self.get_color_data(self.backend.data['condition'])
        color = condition_color if self.colorize else self.color

        self.output = {
            'full_text': formatp(self.format, **self.backend.data).strip(),
            'color': color,
        }

    def run(self):
        pass
