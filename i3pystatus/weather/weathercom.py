from i3pystatus.core.util import internet, require
from i3pystatus.weather import WeatherBackend

from datetime import datetime
from urllib.request import urlopen
from html.parser import HTMLParser
import json
import re

API_PARAMS = ('api_key', 'lang', 'latitude', 'longitude')

API_URL = 'https://api.weather.com/v2/turbo/vt1precipitation;vt1currentdatetime;vt1pollenforecast;vt1dailyForecast;vt1observation?units=%s&language=%s&geocode=%s,%s&format=json&apiKey=%s'

FORECAST_URL = 'https://weather.com/weather/today/l/%s'


class WeathercomHTMLParser(HTMLParser):
    '''
    Obtain data points required by the Weather.com API which are obtained
    through some other source at runtime and added as <script> elements to the
    page source.
    '''
    def __init__(self, logger, location_code):
        self.logger = logger
        self.location_code = location_code
        for attr in API_PARAMS:
            setattr(self, attr, None)
        # Not required for API call, but still parsed from the forecast page
        self.city_name = ''
        super(WeathercomHTMLParser, self).__init__()

    def safe_eval(self, data):
        '''
        Execute an eval with no builtins and no locals
        '''
        try:
            return eval(data, {'__builtins__': None}, {})
        except Exception as exc:
            self.logger.log(
                5,
                'Failed to eval() data: %s\n\nOriginal data follows:\n%s',
                exc, data
            )
            return {}

    def read_forecast_page(self):
        with urlopen(FORECAST_URL % self.location_code) as content:
            try:
                content_type = dict(content.getheaders())['Content-Type']
                charset = re.search(r'charset=(.*)', content_type).group(1)
            except AttributeError:
                charset = 'utf-8'
            html = content.read().decode(charset)
        try:
            self.feed(html)
        except Exception as exc:
            self.logger.debug(
                'Exception raised while parsing forecast page',
                exc
            )

    def handle_data(self, content):
        try:
            tag_text = self.get_starttag_text().lower()
        except AttributeError:
            tag_text = ''
        if tag_text == '<script>':
            if 'apiKey' in content:
                # Key is part of a javascript data structure which looks
                # similar to the following:
                #
                # 'sunTurbo': {
                #     'baseUrl': 'https://api.weather.com',
                #     'apiKey': 'c1ea9f47f6a88b9acb43aba7faf389d4',
                #     'locale': 'en-US' || 'en-us'
                # }
                #
                # For our purposes this is close enough to a Python data
                # structure such that it should be able to be eval'ed to a
                # Python dict.
                sunturbo = content.find('\'sunTurbo\'')
                if sunturbo != -1:
                    # Look for the left curly brace after the 'sunTurbo' key
                    lbrace = content.find('{', sunturbo)
                    if lbrace != -1:
                        # Now look for the right curly brace
                        rbrace = content.find('}', lbrace)
                        if rbrace != -1:
                            api_info = content[lbrace:rbrace + 1]
                            # Change '||' to 'or' to allow it to be eval'ed
                            api_info = api_info.replace('||', 'or')
                            api_data = self.safe_eval(api_info)
                            for attr, key in (('api_key', 'apiKey'),
                                              ('lang', 'locale')):
                                try:
                                    setattr(self, attr, api_data[key])
                                except (KeyError, TypeError):
                                    self.logger.debug(
                                        '\'%s\' key not present in %s',
                                        key, api_data
                                    )
            if 'explicit_location' in content and self.location_code in content:
                lbrace = content.find('{')
                rbrace = content.rfind('}')
                if lbrace != rbrace != -1:
                    loc_data = json.loads(content[lbrace:rbrace + 1])
                    for attr, key in (('latitude', 'lat'),
                                      ('longitude', 'long'),
                                      ('city_name', 'prsntNm')):
                        try:
                            setattr(self, attr, loc_data[key])
                        except (KeyError, TypeError):
                            self.logger.debug('\'%s\' key not present in %s',
                                              key, loc_data)


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

    # This will be set once weather data has been checked
    forecast_url = None

    @require(internet)
    def init(self):
        if self.location_code is None:
            raise RuntimeError('A location_code is required')
        self.location_code = str(self.location_code)
        if ':' in self.location_code:
            # Set the URL so that clicking the weather will launch the
            # weather.com forecast page. Only set it though if there is a colon
            # in the location_code. Technically, the weather.com API will
            # successfully return weather data if a U.S. ZIP code is used as
            # the location_code (e.g. 94107), but if substituted in
            # FORECAST_URl it may or may not result in a valid URL.
            self.forecast_url = FORECAST_URL % self.location_code

        parser = WeathercomHTMLParser(self.logger, self.location_code)
        parser.read_forecast_page()

        for attr in API_PARAMS:
            value = getattr(parser, attr, None)
            if value is None:
                raise RuntimeError(
                    'Unable to parse %s from forecast page' % attr)
            setattr(self, attr, value)
        self.city_name = parser.city_name

        units = 'e' if self.units == 'imperial' or self.units == '' else 'm'
        self.url = API_URL % (
            'e' if self.units in ('imperial', '') else 'm',
            self.lang, self.latitude, self.longitude, self.api_key
        )

    def check_response(self, response):
        # Errors for weather.com API manifest in HTTP error codes, not in the
        # JSON response.
        return False

    @require(internet)
    def check_weather(self):
        '''
        Fetches the current weather from wxdata.weather.com service.
        '''
        self.data['update_error'] = ''
        try:
            response = self.api_request(self.url)
            if not response:
                self.data['update_error'] = self.update_error
                return

            observed = response.get('vt1observation', {})
            forecast = response.get('vt1dailyForecast', {})

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
                high_temp = forecast.get('day', {}).get('temperature', [])[0]
            except (AttributeError, IndexError):
                high_temp = ''
            else:
                if high_temp is None:
                    # In the mid-afternoon, the high temp disappears from the
                    # forecast, so just set high_temp to an empty string.
                    high_temp = ''

            try:
                low_temp = forecast.get('night', {}).get('temperature', [])[0]
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
