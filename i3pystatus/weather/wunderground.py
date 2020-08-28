import re
from datetime import datetime
from urllib.request import Request, urlopen

from i3pystatus.core.util import internet, require
from i3pystatus.weather import WeatherBackend


class Wunderground(WeatherBackend):
    '''
    This module retrieves weather data from Weather Underground.

    .. note::
        Previous versions of this module required an API key to work. Weather
        Underground has since discontinued their API, and this module has been
        rewritten to reflect that.

    .. rubric:: Finding your weather station

    To use this module, you must provide a weather station code (as the
    ``location_code`` option). To find your weather station, first search for
    your city and click to view the current conditions. Below the city name you
    will see the station name, and to the right of that a ``CHANGE`` link.
    Clicking that link will display a map, where you can find the station
    closest to you. Clicking on that station will take you back to the current
    conditions page. The weather station code will now be the last part of the
    URL. For example:

    .. code-block:: text

        https://www.wunderground.com/weather/us/ma/cambridge/KMACAMBR4

    In this case, the weather station code would be ``KMACAMBR4``.

    .. _weather-usage-wunderground:

    .. rubric:: Usage example

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.weather import wunderground

        status = Status(logfile='/home/username/var/i3pystatus.log')

        status.register(
            'weather',
            format='{condition} {current_temp}{temp_unit}[ {icon}][ Hi: {high_temp}][ Lo: {low_temp}][ {update_error}]',
            colorize=True,
            hints={'markup': 'pango'},
            backend=wunderground.Wunderground(
                location_code='KMACAMBR4',
                units='imperial',
                update_error='<span color="#ff0000">!</span>',
            ),
        )

        status.run()

    See :ref:`here <weather-formatters>` for a list of formatters which can be
    used.
    '''
    settings = (
        ('location_code', 'Location code from wunderground.com'),
        ('units', '\'metric\' or \'imperial\''),
        ('update_error', 'Value for the ``{update_error}`` formatter when an '
                         'error is encountered while checking weather data'),
    )

    required = ('location_code',)

    location_code = None
    units = 'metric'
    update_error = '!'

    summary_url = 'https://api.weather.com/v2/pws/dailysummary/1day?apiKey={api_key}&stationId={location_code}&format=json&units={units_type}'
    observation_url = 'https://api.weather.com/v2/pws/observations/current?apiKey={api_key}&stationId={location_code}&format=json&units={units_type}'
    overview_url = 'https://api.weather.com/v3/aggcommon/v3alertsHeadlines;v3-wx-observations-current;v3-location-point?apiKey={api_key}&geocodes={lat:.2f}%2C{lon:.2f}&language=en-US&units=e&format=json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0',
        'Referer': 'https://www.wunderground.com/dashboard/pws/{location_code}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    def init(self):
        self.units_type = 'm' if self.units == 'metric' else 'e'

    @require(internet)
    def get_api_key(self):
        '''
        Grab the API key out of the page source from the home page
        '''
        url = 'https://www.wunderground.com'
        try:
            page_source = self.http_request(
                url,
                headers={
                    'User-Agent': self.headers['User-Agent'],
                    'Accept-Language': self.headers['Accept-Language'],
                    'Conncetion': self.headers['Connection'],
                },
            )
        except Exception as exc:
            self.logger.exception('Failed to load %s', url)
        else:
            try:
                return re.search(r'apiKey=([0-9a-f]+)', page_source).group(1)
            except AttributeError:
                self.logger.error('Failed to find API key in mainpage source')

    @require(internet)
    def api_request(self, url, headers=None):
        if headers is None:
            headers = {}
        return super(Wunderground, self).api_request(
            url,
            headers=dict([(k, v.format(**vars(self))) for k, v in headers.items()]))

    @require(internet)
    def check_weather(self):
        '''
        Query the desired station and return the weather data
        '''
        # Get the API key from the page source
        self.api_key = self.get_api_key()
        if self.api_key is None:
            self.data['update_error'] = self.update_error
            return

        self.data['update_error'] = ''
        try:
            try:
                summary = self.api_request(self.summary_url.format(**vars(self)))['summaries'][0]
            except (IndexError, KeyError):
                self.logger.error(
                    'Failed to retrieve summary data from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            try:
                observation = self.api_request(self.observation_url.format(**vars(self)))['observations'][0]
            except (IndexError, KeyError):
                self.logger.error(
                    'Failed to retrieve observation data from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            self.lat = observation['lat']
            self.lon = observation['lon']

            try:
                overview = self.api_request(self.overview_url.format(**vars(self)))[0]
            except IndexError:
                self.logger.error(
                    'Failed to retrieve overview data from API response. '
                    'Run module with debug logging to get more information.'
                )
                self.data['update_error'] = self.update_error
                return

            if self.units == 'metric':
                temp_unit = '°C'
                speed_unit = 'kph'
                distance_unit = 'km'
                pressure_unit = 'mb'
            else:
                temp_unit = '°F'
                speed_unit = 'mph'
                distance_unit = 'mi'
                pressure_unit = 'in'

            try:
                observation_time_str = observation.get('obsTimeLocal', '')
                observation_time = datetime.strptime(observation_time_str,
                                                     '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                observation_time = datetime.fromtimestamp(0)

            def _find(path, data, default=''):
                ptr = data
                try:
                    for item in path.split(':'):
                        if item == 'units':
                            item = self.units
                        ptr = ptr[item]
                except (KeyError, IndexError, TypeError):
                    return default
                return str(ptr)

            pressure_tendency = _find(
                'v3-wx-observations-current:pressureTendencyTrend',
                overview).lower()
            pressure_trend = '+' if pressure_tendency == 'rising' else '-'

            self.data['city'] = _find('v3-location-point:location:city', overview)
            self.data['condition'] = _find('v3-wx-observations-current:wxPhraseShort', overview)
            self.data['observation_time'] = observation_time
            self.data['current_temp'] = _find('units:temp', observation, '0')
            self.data['low_temp'] = _find('units:tempLow', summary)
            self.data['high_temp'] = _find('units:tempHigh', summary)
            self.data['temp_unit'] = temp_unit
            self.data['feelslike'] = _find('units:heatIndex', observation)
            self.data['dewpoint'] = _find('units:dewpt', observation)
            self.data['wind_speed'] = _find('units:windSpeed', observation)
            self.data['wind_unit'] = speed_unit
            self.data['wind_direction'] = _find('v3-wx-observations-current:windDirectionCardinal', overview)
            self.data['wind_gust'] = _find('units:windGust', observation)
            self.data['pressure'] = _find('units:pressure', observation)
            self.data['pressure_unit'] = pressure_unit
            self.data['pressure_trend'] = pressure_trend
            self.data['visibility'] = _find('v3-wx-observations-current:visibility', overview)
            self.data['visibility_unit'] = distance_unit
            self.data['humidity'] = _find('humidity', observation)
            self.data['uv_index'] = _find('uv', observation)
        except Exception:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking weather. '
                'Exception follows:', exc_info=True
            )
            self.data['update_error'] = self.update_error
