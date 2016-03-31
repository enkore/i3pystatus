from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require

from datetime import datetime
from urllib.request import urlopen
import json
import re

GEOLOOKUP_URL = 'http://api.wunderground.com/api/%s/geolookup%s/q/%s.json'
STATION_QUERY_URL = 'http://api.wunderground.com/api/%s/%s/q/%s.json'


class Wunderground(IntervalModule):
    '''
    This module retrieves weather data using the Weather Underground API.

    .. note::
        A Weather Underground API key is required to use this module, you can
        sign up for a developer API key free at
        https://www.wunderground.com/weather/api/

        A developer API key is allowed 500 queries per day, and no more than 10
        in a given minute. Therefore, it is recommended to be conservative when
        setting the update interval.

        Valid values for ``location_code`` include:

        * **State/City_Name** - CA/San_Francisco
        * **Country/City** - France/Paris
        * **Geolocation by IP** - autoip
        * **Zip or Postal Code** - 60616
        * **ICAO Airport Code** - icao:LAX
        * **Latitude/Longitude** - 41.8301943,-87.6342619
        * **Personal Weather Station (PWS)** - pws:KILCHICA30

        When not using a ``pws`` or ``icao`` station ID, the location will be
        queried, and the closest station will be used. For a list of PWS
        station IDs, visit the following URL:

        http://www.wunderground.com/weatherstation/ListStations.asp

    .. _weather-usage-wunderground:

    .. rubric:: Usage example

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.weather import wunderground

        status = Status()

        status.register(
            'weather',
            format='{condition} {current_temp}{temp_unit}{icon}[ Hi: {high_temp}] Lo: {low_temp}',
            colorize=True,
            backend=wunderground.Wunderground(
                api_key='dbafe887d56ba4ad',
                location_code='pws:MAT645',
                units='imperial',
            ),
        )

        status.run()

    See :ref:`here <weather-formatters>` for a list of formatters which can be
    used.
    '''

    interval = 300

    settings = (
        ('api_key', 'Weather Underground API key'),
        ('location_code', 'Location code from wunderground.com'),
        ('units', '\'metric\' or \'imperial\''),
        ('use_pws', 'Set to False to use only airport stations'),
        ('forecast', 'Set to ``True`` to check forecast (generates one '
                     'additional API request per weather update). If set to '
                     '``False``, then the ``low_temp`` and ``high_temp`` '
                     'formatters will be set to empty strings.'),
    )

    required = ('api_key', 'location_code')

    api_key = None
    location_code = None
    units = 'metric'
    use_pws = True
    forecast = False

    # These will be set once weather data has been checked
    station_id = None
    forecast_url = None

    @require(internet)
    def api_request(self, url):
        '''
        Execute an HTTP POST to the specified URL and return the content
        '''
        with urlopen(url) as content:
            try:
                content_type = dict(content.getheaders())['Content-Type']
                charset = re.search(r'charset=(.*)', content_type).group(1)
            except AttributeError:
                charset = 'utf-8'
            response = json.loads(content.read().decode(charset))
            try:
                raise Exception(response['response']['error']['description'])
            except KeyError:
                pass
            return response

    @require(internet)
    def geolookup(self):
        '''
        Use the location_code to perform a geolookup and find the closest
        station. If the location is a pws or icao station ID, no lookup will be
        peformed.
        '''
        if self.station_id is None:
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
                raise Exception('No locations matched location_code %s'
                                % self.location_code)

            if self.use_pws:
                nearest_pws = nearest.get('id', '')
                if not nearest_pws:
                    raise Exception('No id entry for station')
                self.station_id = 'pws:%s' % nearest_pws
            else:
                nearest_airport = nearest.get('icao', '')
                if not nearest_airport:
                    raise Exception('No icao entry for station')
                self.station_id = 'icao:%s' % nearest_airport

    @require(internet)
    def get_forecast(self):
        '''
        If configured to do so, make an API request to retrieve the forecast
        data for the configured/queried weather station, and return the low and
        high temperatures. Otherwise, return two empty strings.
        '''
        if self.forecast:
            query_url = STATION_QUERY_URL % (self.api_key,
                                             'forecast',
                                             self.station_id)
            try:
                response = self.api_request(query_url)['forecast']
                response = response['simpleforecast']['forecastday'][0]
            except (KeyError, IndexError, TypeError):
                raise Exception('No forecast data found for %s' % self.station_id)

            unit = 'celsius' if self.units == 'metric' else 'fahrenheit'
            low_temp = response.get('low', {}).get(unit, '')
            high_temp = response.get('high', {}).get(unit, '')
            return low_temp, high_temp
        else:
            return '', ''

    @require(internet)
    def weather_data(self):
        '''
        Query the configured/queried station and return the weather data
        '''
        # If necessary, do a geolookup to set the station_id
        self.geolookup()

        query_url = STATION_QUERY_URL % (self.api_key,
                                         'conditions',
                                         self.station_id)
        try:
            response = self.api_request(query_url)['current_observation']
            self.forecast_url = response.pop('ob_url', None)
        except KeyError:
            raise Exception('No weather data found for %s' % self.station_id)

        low_temp, high_temp = self.get_forecast()

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

        def _find(key, data=None):
            data = data or response
            return data.get(key, 'N/A')

        try:
            observation_time = int(_find('observation_epoch'))
        except TypeError:
            observation_time = 0

        return dict(
            city=_find('city', response['observation_location']),
            condition=_find('weather'),
            observation_time=datetime.fromtimestamp(observation_time),
            current_temp=_find('temp_' + temp_unit),
            low_temp=low_temp,
            high_temp=high_temp,
            temp_unit='°' + temp_unit.upper(),
            feelslike=_find('feelslike_' + temp_unit),
            dewpoint=_find('dewpoint_' + temp_unit),
            wind_speed=_find('wind_' + speed_unit),
            wind_unit=speed_unit,
            wind_direction=_find('wind_dir'),
            wind_gust=_find('wind_gust_' + speed_unit),
            pressure=_find('pressure_' + pressure_unit),
            pressure_unit=pressure_unit,
            pressure_trend=_find('pressure_trend'),
            visibility=_find('visibility_' + distance_unit),
            visibility_unit=distance_unit,
            humidity=_find('relative_humidity').rstrip('%'),
            uv_index=_find('uv'),
        )
