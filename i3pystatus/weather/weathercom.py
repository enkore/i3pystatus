from i3pystatus.core.util import internet, require
from i3pystatus.weather import WeatherBackend

from datetime import datetime
from urllib.request import urlopen
from html.parser import HTMLParser
import json
import re

WEATHER_URL = 'https://weather.com/weather/today/l/%s'


class WeathercomHTMLParser(HTMLParser):
    '''
    Obtain data points required by the Weather.com API which are obtained
    through some other source at runtime and added as <script> elements to the
    page source.
    '''
    def __init__(self, logger, location_code):
        self.logger = logger
        self.location_code = location_code
        super(WeathercomHTMLParser, self).__init__()

    def get_weather_data(self):
        url = WEATHER_URL % self.location_code
        self.logger.debug('Making request to %s to retrieve weather data', url)
        self.weather_data = None
        with urlopen(url) as content:
            try:
                content_type = dict(content.getheaders())['Content-Type']
                charset = re.search(r'charset=(.*)', content_type).group(1)
            except AttributeError:
                charset = 'utf-8'
            html = content.read().decode(charset)
        try:
            self.feed(html)
        except Exception:
            self.logger.exception(
                'Exception raised while parsing forecast page',
                exc_info=True
            )

    def handle_data(self, content):
        try:
            tag_text = self.get_starttag_text().lower()
        except AttributeError:
            tag_text = ''
        if tag_text.startswith('<script'):
            for line in content.splitlines():
                line = line.strip()
                if line.startswith('var adaptorParams'):
                    # Strip off the "var adaptorParams = " from the beginning,
                    # and the javascript semicolon from the end. This will give
                    # us JSON that we can load.
                    line = line.split('=', 1)[1].lstrip().rstrip(';')
                    self.logger.debug('Loading the following data as JSON: %s', line)
                    try:
                        self.weather_data = json.loads(line)
                    except json.decoder.JSONDecodeError as exc:
                        self.logger.error('Error loading JSON: %s', exc)
                    break


class Weathercom(WeatherBackend):
    '''
    This module gets the weather from weather.com. The ``location_code``
    parameter should be set to the location code from weather.com. To obtain
    this code, search for the location on weather.com, and the location code
    will be everything after the last slash (e.g. ``94107:4:US``).

    .. _weather-usage-weathercom:

    .. rubric:: Usage example

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.weather import weathercom

        status = Status(logfile='/home/username/var/i3pystatus.log')

        status.register(
            'weather',
            format='{condition} {current_temp}{temp_unit}[ {icon}][ Hi: {high_temp}][ Lo: {low_temp}][ {update_error}]',
            interval=900,
            colorize=True,
            hints={'markup': 'pango'},
            backend=weathercom.Weathercom(
                location_code='94107:4:US',
                units='imperial',
                update_error='<span color="#ff0000">!</span>',
            ),
        )

        status.run()

    See :ref:`here <weather-formatters>` for a list of formatters which can be
    used.
    '''
    settings = (
        ('location_code', 'Location code from www.weather.com'),
        ('units', '\'metric\' or \'imperial\''),
        ('update_error', 'Value for the ``{update_error}`` formatter when an '
                         'error is encountered while checking weather data'),
    )
    required = ('location_code',)

    location_code = None
    units = 'metric'
    update_error = '!'

    # This will be set in the init based on the passed location code
    forecast_url = None

    @require(internet)
    def init(self):
        if self.location_code is not None:
            # Ensure that the location code is a string, in the event that a
            # ZIP code (or other all-numeric code) is passed as a non-string.
            self.location_code = str(self.location_code)
            self.forecast_url = WEATHER_URL % self.location_code
        self.parser = WeathercomHTMLParser(self.logger, self.location_code)

    def check_response(self, response):
        # Errors for weather.com API manifest in HTTP error codes, not in the
        # JSON response.
        return False

    @require(internet)
    def check_weather(self):
        '''
        Fetches the current weather from wxdata.weather.com service.
        '''
        if self.location_code is None:
            self.logger.error(
                'A location_code is required to check Weather.com. See the '
                'documentation for more information.'
            )
            self.data['update_error'] = self.update_error
            return
        self.data['update_error'] = ''
        try:

            self.parser.get_weather_data()
            if self.parser.weather_data is None:
                self.logger.error(
                    'Failed to read weather data from page. Run module with '
                    'debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                observed = self.parser.weather_data['observation']['data']['vt1observation']
            except KeyError:
                self.logger.error(
                    'Failed to retrieve current conditions from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                forecast = self.parser.weather_data['dailyForecast']['data']['vt1dailyForecast'][0]
            except (IndexError, KeyError):
                self.logger.error(
                    'Failed to retrieve forecast data from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                self.city_name = self.parser.weather_data['location']['prsntNm']
            except KeyError:
                self.logger.warning(
                    'Failed to get city name from API response, falling back '
                    'to location code \'%s\'', self.location_code
                )
                self.city_name = self.location_code

            # Cut off the timezone from the end of the string (it's after the last
            # space, hence the use of rpartition). International timezones (or ones
            # outside the system locale) don't seem to be handled well by
            # datetime.datetime.strptime().
            try:
                observation_time_str = str(observed.get('observationTime', ''))
                observation_time = datetime.strptime(observation_time_str,
                                                     '%Y-%d-%yT%H:%M:%S%z')
            except (ValueError, AttributeError):
                observation_time = datetime.fromtimestamp(0)

            try:
                pressure_trend_str = observed.get('barometerTrend', '').lower()
            except AttributeError:
                pressure_trend_str = ''

            if pressure_trend_str == 'rising':
                pressure_trend = '+'
            elif pressure_trend_str == 'falling':
                pressure_trend = '-'
            else:
                pressure_trend = ''

            try:
                high_temp = forecast.get('day', {}).get('temperature', '')
            except (AttributeError, IndexError):
                high_temp = ''
            else:
                if high_temp is None:
                    # In the mid-afternoon, the high temp disappears from the
                    # forecast, so just set high_temp to an empty string.
                    high_temp = ''

            try:
                low_temp = forecast.get('night', {}).get('temperature', '')
            except (AttributeError, IndexError):
                low_temp = ''

            if self.units == 'imperial':
                temp_unit = '°F'
                wind_unit = 'mph'
                pressure_unit = 'in'
                visibility_unit = 'mi'
            else:
                temp_unit = '°C'
                wind_unit = 'kph'
                pressure_unit = 'mb'
                visibility_unit = 'km'

            self.data['city'] = self.city_name
            self.data['condition'] = str(observed.get('phrase', ''))
            self.data['observation_time'] = observation_time
            self.data['current_temp'] = str(observed.get('temperature', ''))
            self.data['low_temp'] = str(low_temp)
            self.data['high_temp'] = str(high_temp)
            self.data['temp_unit'] = temp_unit
            self.data['feelslike'] = str(observed.get('feelsLike', ''))
            self.data['dewpoint'] = str(observed.get('dewPoint', ''))
            self.data['wind_speed'] = str(observed.get('windSpeed', ''))
            self.data['wind_unit'] = wind_unit
            self.data['wind_direction'] = str(observed.get('windDirCompass', ''))
            # Gust can be None, using "or" to ensure empty string in this case
            self.data['wind_gust'] = str(observed.get('gust', '') or '')
            self.data['pressure'] = str(observed.get('altimeter', ''))
            self.data['pressure_unit'] = pressure_unit
            self.data['pressure_trend'] = pressure_trend
            self.data['visibility'] = str(observed.get('visibility', ''))
            self.data['visibility_unit'] = visibility_unit
            self.data['humidity'] = str(observed.get('humidity', ''))
            self.data['uv_index'] = str(observed.get('uvIndex', ''))
        except Exception:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking weather. '
                'Exception follows:', exc_info=True
            )
            self.data['update_error'] = self.update_error
