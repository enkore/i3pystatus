from i3pystatus.core.util import internet, require
from i3pystatus.weather import Backend

from datetime import datetime
from urllib.request import urlopen
import re
import xml.etree.ElementTree as ElementTree

WEATHER_COM_URL = \
    'http://wxdata.weather.com/wxdata/weather/local/%s?unit=%s&dayf=1&cc=*'
ON_LEFTCLICK_URL = 'https://weather.com/weather/today/l/%s'


class Weathercom(Backend):
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

        status = Status()

        status.register(
            'weather',
            format='{condition} {current_temp}{temp_unit}{icon}\
[ Hi: {high_temp}] Lo: {low_temp}',
            colorize=True,
            backend=weathercom.Weathercom(
                location_code='94107:4:US',
                units='imperial',
            ),
        )

        status.run()

    See :ref:`here <weather-formatters>` for a list of formatters which can be
    used.
    '''
    settings = (
        ('location_code', 'Location code from www.weather.com'),
        ('units', '\'metric\' or \'imperial\''),
    )
    required = ('location_code',)

    location_code = None

    units = 'metric'

    # This will be set once weather data has been checked
    forecast_url = None

    @require(internet)
    def weather_data(self):
        '''
        Fetches the current weather from wxdata.weather.com service.
        '''
        if self.forecast_url is None and ':' in self.location_code:
            # Set the URL so that clicking the weather will launch the
            # weather.com forecast page. Only set it though if there is a colon
            # in the location_code. Technically, the weather.com API will
            # successfully return weather data if a U.S. ZIP code is used as
            # the location_code (e.g. 94107), but if substituted in
            # ON_LEFTCLICK_URL it may or may not result in a valid URL.
            self.forecast_url = ON_LEFTCLICK_URL % self.location_code

        unit = '' if self.units == 'imperial' or self.units == '' else 'm'
        url = WEATHER_COM_URL % (self.location_code, unit)
        with urlopen(url) as handler:
            try:
                content_type = dict(handler.getheaders())['Content-Type']
                charset = re.search(r'charset=(.*)', content_type).group(1)
            except AttributeError:
                charset = 'utf-8'
            xml = handler.read().decode(charset)
        doc = ElementTree.XML(xml)

        # Cut off the timezone from the end of the string (it's after the last
        # space, hence the use of rpartition). International timezones (or ones
        # outside the system locale) don't seem to be handled well by
        # datetime.datetime.strptime().
        try:
            observation_time_str = doc.findtext('cc/lsup').rpartition(' ')[0]
            observation_time = datetime.strptime(observation_time_str,
                                                 '%m/%d/%y %I:%M %p')
        except (ValueError, AttributeError):
            observation_time = datetime.fromtimestamp(0)

        pressure_trend_str = doc.findtext('cc/bar/d').lower()
        if pressure_trend_str == 'rising':
            pressure_trend = '+'
        elif pressure_trend_str == 'falling':
            pressure_trend = '-'
        else:
            pressure_trend = ''

        if not doc.findtext('dayf/day[@d="0"]/part[@p="d"]/icon').strip():
            # If the "d" (day) part of today's forecast's keys are empty, there
            # is no high temp anymore (this happens in the afternoon), but
            # instead of handling things in a sane way and setting the high
            # temp to an empty string or something like that, the API returns
            # the current temp as the high temp, which is incorrect. This if
            # statement catches it so that we can correctly report that there
            # is no high temp at this point of the day.
            high_temp = ''
        else:
            high_temp = doc.findtext('dayf/day[@d="0"]/hi')

        return dict(
            city=doc.findtext('loc/dnam'),
            condition=doc.findtext('cc/t'),
            observation_time=observation_time,
            current_temp=doc.findtext('cc/tmp'),
            low_temp=doc.findtext('dayf/day[@d="0"]/low'),
            high_temp=high_temp,
            temp_unit='°' + doc.findtext('head/ut').upper(),
            feelslike=doc.findtext('cc/flik'),
            dewpoint=doc.findtext('cc/dewp'),
            wind_speed=doc.findtext('cc/wind/s'),
            wind_unit=doc.findtext('head/us'),
            wind_direction=doc.findtext('cc/wind/t'),
            wind_gust=doc.findtext('cc/wind/gust'),
            pressure=doc.findtext('cc/bar/r'),
            pressure_unit=doc.findtext('head/up'),
            pressure_trend=pressure_trend,
            visibility=doc.findtext('cc/vis'),
            visibility_unit=doc.findtext('head/ud'),
            humidity=doc.findtext('cc/hmid'),
            uv_index=doc.findtext('cc/uv/i'),
        )
