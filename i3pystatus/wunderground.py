from i3pystatus import IntervalModule
from i3pystatus.core.util import user_open, internet, require

from datetime import datetime
from urllib.request import urlopen
import json
import re

GEOLOOKUP_URL = 'http://api.wunderground.com/api/%s/geolookup%s/q/%s.json'
STATION_LOOKUP_URL = 'http://api.wunderground.com/api/%s/conditions/q/%s.json'


class Wunderground(IntervalModule):
    '''
    This module retrieves weather from the Weather Underground API.

    .. note::
        A Weather Underground API key is required to use this module, you can
        sign up for one for a developer API key free at
        https://www.wunderground.com/weather/api/

        A developer API key is allowed 500 queries per day.

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

    .. rubric:: Available formatters

    * `{city}` — Location of weather observation
    * `{conditon}` — Current condition (Rain, Snow, Overcast, etc.)
    * `{observation_time}` — Time of weather observation (supports strftime format flags)
    * `{current_temp}` — Current temperature, excluding unit
    * `{degrees}` — ``°C`` if ``units`` is set to ``metric``, otherwise ``°F``
    * `{feelslike}` — Wunderground "Feels Like" temperature, excluding unit
    * `{current_wind}` — Wind speed in mph/kph, excluding unit
    * `{current_wind_direction}` — Wind direction
    * `{current_wind_gust}` — Speed of wind gusts in mph/kph, excluding unit
    * `{pressure_in}` — Barometric pressure (in inches), excluding unit
    * `{pressure_mb}` — Barometric pressure (in millibars), excluding unit
    * `{pressure_trend}` — ``+`` (rising) or ``-`` (falling)
    * `{visibility}` — Visibility in mi/km, excluding unit
    * `{humidity}` — Current humidity, excluding percentage symbol
    * `{dewpoint}` — Dewpoint temperature, excluding unit
    * `{uv_index}` — UV Index

    '''

    interval = 300

    settings = (
        ('api_key', 'Weather Underground API key'),
        ('location_code', 'Location code from www.weather.com'),
        ('units', 'Celsius (metric) or Fahrenheit (imperial)'),
        ('use_pws', 'Set to False to use only airport stations'),
        ('error_log', 'If set, tracebacks will be logged to this file'),
        'format',
    )
    required = ('api_key', 'location_code')

    api_key = None
    location_code = None
    units = "metric"
    format = "{current_temp}{degrees}"
    use_pws = True
    error_log = None

    station_id = None
    forecast_url = None

    on_leftclick = 'open_wunderground'

    def open_wunderground(self):
        '''
        Open the forecast URL, if one was retrieved
        '''
        if self.forecast_url and self.forecast_url != 'N/A':
            user_open(self.forecast_url)

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

    def query_station(self):
        '''
        Query a specific station
        '''
        # If necessary, do a geolookup to set the station_id
        self.geolookup()

        query_url = STATION_LOOKUP_URL % (self.api_key, self.station_id)
        try:
            response = self.api_request(query_url)['current_observation']
            self.forecast_url = response.pop('forecast_url', None)
        except KeyError:
            raise Exception('No weather data found for %s' % self.station_id)

        def _find(key, data=None):
            data = data or response
            return data.get(key, 'N/A')

        if self.units == 'metric':
            temp_unit = 'c'
            speed_unit = 'kph'
            distance_unit = 'km'
        else:
            temp_unit = 'f'
            speed_unit = 'mph'
            distance_unit = 'mi'

        try:
            observation_time = int(_find('observation_epoch'))
        except TypeError:
            observation_time = 0

        return dict(
            forecast_url=_find('forecast_url'),
            city=_find('city', response['observation_location']),
            condition=_find('weather'),
            observation_time=datetime.fromtimestamp(observation_time),
            current_temp=_find('temp_' + temp_unit),
            feelslike=_find('feelslike_' + temp_unit),
            current_wind=_find('wind_' + speed_unit),
            current_wind_direction=_find('wind_dir'),
            current_wind_gust=_find('wind_gust_' + speed_unit),
            pressure_in=_find('pressure_in'),
            pressure_mb=_find('pressure_mb'),
            pressure_trend=_find('pressure_trend'),
            visibility=_find('visibility_' + distance_unit),
            humidity=_find('relative_humidity').rstrip('%'),
            dewpoint=_find('dewpoint_' + temp_unit),
            uv_index=_find('uv'),
        )

    @require(internet)
    def run(self):
        try:
            result = self.query_station()
        except Exception as exc:
            if self.error_log:
                import traceback
                with open(self.error_log, 'a') as f:
                    f.write('%s : An exception was raised:\n' %
                            datetime.isoformat(datetime.now()))
                    f.write(''.join(traceback.format_exc()))
                    f.write(80 * '-' + '\n')
            raise

        result['degrees'] = '°%s' % ('C' if self.units == 'metric' else 'F')

        self.output = {
            "full_text": self.format.format(**result),
            # "color": self.color  # TODO: add some sort of color effect
        }
