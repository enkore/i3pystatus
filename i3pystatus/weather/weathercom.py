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
                weather_data = None
                self.logger.debug('Located window.__data')
                # Strip the "window.__data=" from the beginning and load json
                json_data = self.load_json(
                    content[begin:].split('=', 1)[1].lstrip()
                )
                if json_data is not None:
                    try:
                        weather_data = json_data['dal']
                    except KeyError:
                        pass

                if weather_data is None:
                    self.logger.debug(
                        'Failed to locate weather data in the '
                        'following data: %s', json_data
                    )
                else:
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
                observed = self.parser.weather_data['getSunV3CurrentObservationsUrlConfig']
                # Observation data stored under a sub-key containing the
                # lat/long coordinates, locale info, etc. For example:
                #
                # geocode:41.77,-88.35:language:en-US:units:e
                #
                # Since this is the only key under "Observation", we can just
                # use next(iter(observed)) to get it.
                observed = observed[next(iter(observed))]['data']
            except KeyError:
                self.logger.error(
                    'Failed to retrieve current conditions from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                forecast = self.parser.weather_data['getSunV3DailyForecastUrlConfig']
                # Same as above, use next(iter(forecast)) to drill down to the
                # correct nested dict level.
                forecast = forecast[next(iter(forecast))]['data']
            except (IndexError, KeyError):
                self.logger.error(
                    'Failed to retrieve forecast data from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                location = self.parser.weather_data['getSunV3LocationPointUrlConfig']
                # Again, same technique as above used to get down to the
                # correct nested dict level.
                location = location[next(iter(location))]
                self.city_name = location['data']['location']['displayName']
            except KeyError:
                self.logger.warning(
                    'Failed to get city name from API response, falling back '
                    'to location code \'%s\'', self.location_code
                )
                self.city_name = self.location_code

            try:
                observation_time_str = str(observed.get('validTimeLocal', ''))
                observation_time = datetime.strptime(observation_time_str,
                                                     '%Y-%d-%yT%H:%M:%S%z')
            except (ValueError, AttributeError):
                observation_time = datetime.fromtimestamp(0)

            try:
                pressure_trend_str = observed.get('pressureTendencyTrend', '').lower()
            except AttributeError:
                pressure_trend_str = ''

            if pressure_trend_str == 'rising':
                pressure_trend = '+'
            elif pressure_trend_str == 'falling':
                pressure_trend = '-'
            else:
                pressure_trend = ''

            self.logger.critical('forecast = %s', forecast)
            try:
                high_temp = forecast.get('temperatureMax', [])[0] or ''
            except (AttributeError, IndexError):
                high_temp = ''

            try:
                low_temp = forecast.get('temperatureMin', [])[0]
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
            self.data['condition'] = str(observed.get('wxPhraseMedium', ''))
            self.data['observation_time'] = observation_time
            self.data['current_temp'] = str(observed.get('temperature', ''))
            self.data['low_temp'] = str(low_temp)
            self.data['high_temp'] = str(high_temp)
            self.data['temp_unit'] = temp_unit
            self.data['feelslike'] = str(observed.get('temperatureFeelsLike', ''))
            self.data['dewpoint'] = str(observed.get('temperatureDewPoint', ''))
            self.data['wind_speed'] = str(observed.get('windSpeed', ''))
            self.data['wind_unit'] = wind_unit
            self.data['wind_direction'] = str(observed.get('windDirectionCardinal', ''))
            # Gust can be None, using "or" to ensure empty string in this case
            self.data['wind_gust'] = str(observed.get('windGust', '') or '')
            self.data['pressure'] = str(observed.get('pressureAltimeter', ''))
            self.data['pressure_unit'] = pressure_unit
            self.data['pressure_trend'] = pressure_trend
            self.data['visibility'] = str(observed.get('visibility', ''))
            self.data['visibility_unit'] = visibility_unit
            self.data['humidity'] = str(observed.get('relativeHumidity', ''))
            self.data['uv_index'] = str(observed.get('uvIndex', ''))
        except Exception:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking weather. '
                'Exception follows:', exc_info=True
            )
            self.data['update_error'] = self.update_error
