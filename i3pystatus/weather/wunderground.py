from i3pystatus.core.util import internet, require
from i3pystatus.weather import WeatherBackend

from datetime import datetime
from urllib.request import urlopen

GEOLOOKUP_URL = 'http://api.wunderground.com/api/%s/geolookup%s/q/%s.json'
STATION_QUERY_URL = 'http://api.wunderground.com/api/%s/%s/q/%s.json'


class Wunderground(WeatherBackend):
    '''
    This module retrieves weather data using the Weather Underground API.

    .. note::
        A Weather Underground API key is required to use this module, you can
        sign up for a developer API key free at
        https://www.wunderground.com/weather/api/

        Valid values for ``location_code`` include:

        * **State/City_Name** - CA/San_Francisco
        * **Country/City** - France/Paris
        * **Geolocation by IP** - autoip
        * **Zip or Postal Code** - 60616
        * **ICAO Airport Code** - icao:LAX
        * **Latitude/Longitude** - 41.8301943,-87.6342619
        * **Personal Weather Station (PWS)** - pws:KILCHICA30

        When not using a ``pws`` or ``icao`` station ID, the location will be
        queried (this uses an API query), and the closest station will be used.
        For a list of PWS station IDs, visit the following URL:

        http://www.wunderground.com/weatherstation/ListStations.asp

        .. rubric:: API usage

        An API key is allowed 500 queries per day, and no more than 10 in a
        given minute. Therefore, it is recommended to be conservative when
        setting the update interval (the default is 1800 seconds, or 30
        minutes), and one should be careful how often one restarts i3pystatus
        and how often a refresh is forced by left-clicking the module.

        As noted above, when not using a ``pws`` or ``icao`` station ID, an API
        query will be used to determine the station ID to use. This will be
        done once when i3pystatus is started, and not repeated until the next
        time i3pystatus is started.

        When updating weather data, one API query will be used to obtain the
        current conditions. The high/low temperature forecast requires an
        additonal API query, and is optional (disabled by default). To enable
        forecast checking, set ``forecast=True``.

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
                api_key='dbafe887d56ba4ad',
                location_code='pws:MAT645',
                units='imperial',
                forecast=True,
                update_error='<span color="#ff0000">!</span>',
            ),
        )

        status.run()

    See :ref:`here <weather-formatters>` for a list of formatters which can be
    used.
    '''
    settings = (
        ('api_key', 'Weather Underground API key'),
        ('location_code', 'Location code from wunderground.com'),
        ('units', '\'metric\' or \'imperial\''),
        ('use_pws', 'Set to False to use only airport stations'),
        ('forecast', 'Set to ``True`` to check forecast (generates one '
                     'additional API request per weather update). If set to '
                     '``False``, then the ``low_temp`` and ``high_temp`` '
                     'formatters will be set to empty strings.'),
        ('update_error', 'Value for the ``{update_error}`` formatter when an '
                         'error is encountered while checking weather data'),
    )

    required = ('api_key', 'location_code')

    api_key = None
    location_code = None
    units = 'metric'
    use_pws = True
    forecast = False
    update_error = '!'

    # These will be set once weather data has been checked
    station_id = None
    forecast_url = None

    @require(internet)
    def init(self):
        '''
        Use the location_code to perform a geolookup and find the closest
        station. If the location is a pws or icao station ID, no lookup will be
        peformed.
        '''
        try:
            for no_lookup in ('pws', 'icao'):
                sid = self.location_code.partition(no_lookup + ':')[-1]
                if sid:
                    self.station_id = self.location_code
                    return
        except AttributeError:
            # Numeric or some other type, either way we'll just stringify
            # it below and perform a lookup.
            pass

        extra_opts = '/pws:0' if not self.use_pws else ''
        api_url = GEOLOOKUP_URL % (self.api_key,
                                   extra_opts,
                                   self.location_code)
        response = self.api_request(api_url)
        station_type = 'pws' if self.use_pws else 'airport'
        try:
            stations = response['location']['nearby_weather_stations']
            nearest = stations[station_type]['station'][0]
        except (KeyError, IndexError):
            raise Exception(
                'No locations matched location_code %s' % self.location_code)

        if self.use_pws:
            nearest_pws = nearest.get('id', '')
            if not nearest_pws:
                raise Exception('No id entry for nearest PWS')
            self.station_id = 'pws:%s' % nearest_pws
        else:
            nearest_airport = nearest.get('icao', '')
            if not nearest_airport:
                raise Exception('No icao entry for nearest airport')
            self.station_id = 'icao:%s' % nearest_airport

    @require(internet)
    def get_forecast(self):
        '''
        If configured to do so, make an API request to retrieve the forecast
        data for the configured/queried weather station, and return the low and
        high temperatures. Otherwise, return two empty strings.
        '''
        no_data = ('', '')
        if self.forecast:
            query_url = STATION_QUERY_URL % (self.api_key,
                                             'forecast',
                                             self.station_id)
            try:
                response = self.api_request(query_url)['forecast']
                response = response['simpleforecast']['forecastday'][0]
            except (KeyError, IndexError, TypeError):
                self.logger.error(
                    'No forecast data found for %s', self.station_id)
                self.data['update_error'] = self.update_error
                return no_data

            unit = 'celsius' if self.units == 'metric' else 'fahrenheit'
            low_temp = response.get('low', {}).get(unit, '')
            high_temp = response.get('high', {}).get(unit, '')
            return low_temp, high_temp
        else:
            return no_data

    def check_response(self, response):
        try:
            return response['response']['error']['description']
        except KeyError:
            # No error in response
            return False

    @require(internet)
    def check_weather(self):
        '''
        Query the configured/queried station and return the weather data
        '''
        self.data['update_error'] = ''
        try:
            query_url = STATION_QUERY_URL % (self.api_key,
                                             'conditions',
                                             self.station_id)
            try:
                response = self.api_request(query_url)['current_observation']
                self.forecast_url = response.pop('ob_url', None)
            except KeyError:
                self.logger.error('No weather data found for %s', self.station_id)
                self.data['update_error'] = self.update_error
                return

            if self.forecast:
                query_url = STATION_QUERY_URL % (self.api_key,
                                                 'forecast',
                                                 self.station_id)
                try:
                    forecast = self.api_request(query_url)['forecast']
                    forecast = forecast['simpleforecast']['forecastday'][0]
                except (KeyError, IndexError, TypeError):
                    self.logger.error(
                        'No forecast data found for %s', self.station_id)
                    # This is a non-fatal error, so don't return but do set the
                    # error flag.
                    self.data['update_error'] = self.update_error

                unit = 'celsius' if self.units == 'metric' else 'fahrenheit'
                low_temp = forecast.get('low', {}).get(unit, '')
                high_temp = forecast.get('high', {}).get(unit, '')
            else:
                low_temp = high_temp = ''

            if self.units == 'metric':
                temp_unit = 'c'
                speed_unit = 'kph'
                distance_unit = 'km'
                pressure_unit = 'mb'
            else:
                temp_unit = 'f'
                speed_unit = 'mph'
                distance_unit = 'mi'
                pressure_unit = 'in'

            def _find(key, data=None, default=''):
                if data is None:
                    data = response
                return str(data.get(key, default))

            try:
                observation_time = datetime.fromtimestamp(
                    int(_find('observation_epoch'))
                )
            except TypeError:
                observation_time = datetime.fromtimestamp(0)

            self.data['city'] = _find('city', response['observation_location'])
            self.data['condition'] = _find('weather')
            self.data['observation_time'] = observation_time
            self.data['current_temp'] = _find('temp_' + temp_unit).split('.')[0]
            self.data['low_temp'] = low_temp
            self.data['high_temp'] = high_temp
            self.data['temp_unit'] = '°' + temp_unit.upper()
            self.data['feelslike'] = _find('feelslike_' + temp_unit)
            self.data['dewpoint'] = _find('dewpoint_' + temp_unit)
            self.data['wind_speed'] = _find('wind_' + speed_unit)
            self.data['wind_unit'] = speed_unit
            self.data['wind_direction'] = _find('wind_dir')
            self.data['wind_gust'] = _find('wind_gust_' + speed_unit)
            self.data['pressure'] = _find('pressure_' + pressure_unit)
            self.data['pressure_unit'] = pressure_unit
            self.data['pressure_trend'] = _find('pressure_trend')
            self.data['visibility'] = _find('visibility_' + distance_unit)
            self.data['visibility_unit'] = distance_unit
            self.data['humidity'] = _find('relative_humidity').rstrip('%')
            self.data['uv_index'] = _find('UV')
        except Exception:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking weather. '
                'Exception follows:', exc_info=True
            )
            self.data['update_error'] = self.update_error
