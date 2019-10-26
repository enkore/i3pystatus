import json
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.request import Request, urlopen

from i3pystatus.core.util import internet, require
from i3pystatus.weather import WeatherBackend

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'


class WeathercomHTMLParser(HTMLParser):
    '''
    Obtain data points required by the Weather.com API which are obtained
    through some other source at runtime and added as <script> elements to the
    page source.
    '''

    def __init__(self, logger):
        self.logger = logger
        super(WeathercomHTMLParser, self).__init__()

    def get_weather_data(self, url):
        self.logger.debug('Making request to %s to retrieve weather data', url)
        self.weather_data = None
        req = Request(url, headers={'User-Agent': USER_AGENT})
        with urlopen(req) as content:
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

    def load_json(self, json_input):
        self.logger.debug('Loading the following data as JSON: %s', json_input)
        try:
            return json.loads(json_input)
        except json.decoder.JSONDecodeError as exc:
            self.logger.debug('Error loading JSON: %s', exc)
            self.logger.debug('String that failed to load: %s', json_input)
        return None

    def handle_data(self, content):
        '''
        Sometimes the weather data is set under an attribute of the "window"
        DOM object. Sometimes it appears as part of a javascript function.
        Catch either possibility.
        '''
        if self.weather_data is not None:
            # We've already found weather data, no need to continue parsing
            return
        content = content.strip().rstrip(';')
        try:
            tag_text = self.get_starttag_text().lower()
        except AttributeError:
            tag_text = ''
        if tag_text.startswith('<script'):
            # Look for feed information embedded as a javascript variable
            begin = content.find('window.__data')
            if begin != -1:
                self.logger.debug('Located window.__data')
                # Look for end of JSON dict and end of javascript statement
                end = content.find('};', begin)
                if end == -1:
                    self.logger.debug('Failed to locate end of javascript statement')
                else:
                    # Strip the "window.__data=" from the beginning
                    json_data = self.load_json(
                        content[begin:end + 1].split('=', 1)[1].lstrip()
                    )
                    if json_data is not None:
                        def _find_weather_data(data):
                            '''
                            Helper designed to minimize impact of potential
                            structural changes to this data.
                            '''
                            if isinstance(data, dict):
                                if 'Observation' in data and 'DailyForecast' in data:
                                    return data
                                else:
                                    for key in data:
                                        ret = _find_weather_data(data[key])
                                        if ret is not None:
                                            return ret
                                return None

                        weather_data = _find_weather_data(json_data)
                        if weather_data is None:
                            self.logger.debug(
                                'Failed to locate weather data in the '
                                'following data structure: %s', json_data
                            )
                        else:
                            self.weather_data = weather_data
                            return

            for line in content.splitlines():
                line = line.strip().rstrip(';')
                if line.startswith('var adaptorParams'):
                    # Strip off the "var adaptorParams = " from the beginning,
                    # and the javascript semicolon from the end. This will give
                    # us JSON that we can load.
                    weather_data = self.load_json(line.split('=', 1)[1].lstrip())
                    if weather_data is not None:
                        self.weather_data = weather_data
                        return


class Weathercom(WeatherBackend):
    '''
    This module gets the weather from weather.com. The ``location_code``
    parameter should be set to the location code from weather.com. To obtain
    this code, search for your location on weather.com, and when you go to the
    forecast page, the code you need will be everything after the last slash in
    the URL (e.g. ``94107:4:US``).

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

    url_template = 'https://weather.com/{locale}/weather/today/l/{location_code}'

    # This will be set in the init based on the passed location code
    forecast_url = None

    def init(self):
        if self.location_code is not None:
            # Ensure that the location code is a string, in the event that a
            # ZIP code (or other all-numeric code) is passed as a non-string.
            self.location_code = str(self.location_code)

        # Setting the locale to en-AU returns units in metric. Leaving it blank
        # causes weather.com to return the default, which is imperial.
        self.locale = 'en-AU' if self.units == 'metric' else ''

        self.forecast_url = self.url_template.format(**vars(self))
        self.parser = WeathercomHTMLParser(self.logger)

    def check_response(self, response):
        # Errors for weather.com API manifest in HTTP error codes, not in the
        # JSON response.
        return False

    @require(internet)
    def check_weather(self):
        '''
        Fetches the current weather from wxdata.weather.com service.
        '''

        if self.units not in ('imperial', 'metric'):
            raise Exception("units must be one of (imperial, metric)!")

        if self.location_code is None:
            self.logger.error(
                'A location_code is required to check Weather.com. See the '
                'documentation for more information.'
            )
            self.data['update_error'] = self.update_error
            return
        self.data['update_error'] = ''
        try:

            self.parser.get_weather_data(self.forecast_url)
            if self.parser.weather_data is None:
                self.logger.error(
                    'Failed to read weather data from page. Run module with '
                    'debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                observed = self.parser.weather_data['Observation']
                # Observation data stored under a sub-key containing the
                # lat/long coordinates. For example:
                #
                # geocode:41.77,-88.35:language:en-US:units:e
                #
                # Since this is the only key under "Observation", we can just
                # use next(iter(observed)) to get it.
                observed = observed[next(iter(observed))]['data']['vt1observation']
            except KeyError:
                self.logger.error(
                    'Failed to retrieve current conditions from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                forecast = self.parser.weather_data['DailyForecast']
                # Same as above, use next(iter(forecast)) to drill down to the
                # correct nested dict level.
                forecast = forecast[next(iter(forecast))]
                forecast = forecast['data']['vt1dailyForecast'][0]
            except (IndexError, KeyError):
                self.logger.error(
                    'Failed to retrieve forecast data from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                self.city_name = self.parser.weather_data['Location']
                # Again, same technique as above used to get down to the
                # correct nested dict level.
                self.city_name = self.city_name[next(iter(self.city_name))]
                self.city_name = self.city_name['data']['location']['displayName']
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
