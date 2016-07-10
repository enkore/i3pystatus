from i3pystatus import SettingsBase, IntervalModule, formatp
from i3pystatus.core.util import user_open, internet, require


class Backend(SettingsBase):
    settings = ()


class Weather(IntervalModule):
    '''
    This is a generic weather-checker which must use a configured weather
    backend. For list of all available backends see :ref:`weatherbackends`.

    Left clicking on the module will launch the forecast page for the location
    being checked.

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

    This module supports the :ref:`formatp <formatp>` extended string format
    syntax. This allows for values to be hidden when they evaluate as False.
    This comes in handy for the :py:mod:`weathercom <.weather.weathercom>`
    backend, which at a certain point in the afternoon will have a blank
    ``{high_temp}`` value. Using the following snippet in your format string
    will only display the high temperature information if it is not blank:

    ::

        {current_temp}{temp_unit}[ Hi: {high_temp}[{temp_unit}]] Lo: {low_temp}{temp_unit}

    Brackets are evaluated from the outside-in, so the fact that the only
    formatter in the outer block (``{high_temp}``) is empty would keep the
    inner block from being evaluated at all, and entire block would not be
    displayed.

    See the following links for usage examples for the available weather
    backends:

    - :ref:`Weather.com <weather-usage-weathercom>`
    - :ref:`Weather Underground <weather-usage-wunderground>`
    '''

    settings = (
        ('colorize', 'Vary the color depending on the current conditions.'),
        ('color_icons', 'Dictionary mapping weather conditions to tuples '
                        'containing a UTF-8 code for the icon, and the color '
                        'to be used.'),
        ('color', 'Display color (or fallback color if ``colorize`` is True). '
                  'If not specified, falls back to default i3bar color.'),
        ('backend', 'Weather backend instance'),
        'interval',
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
    format = '{current_temp}{temp_unit}'

    on_leftclick = 'open_forecast_url'

    def open_forecast_url(self):
        if self.backend.forecast_url and self.backend.forecast_url != 'N/A':
            user_open(self.backend.forecast_url)

    def init(self):
        pass

    def get_color_data(self, condition):
        '''
        Disambiguate similarly-named weather conditions, and return the icon
        and color that match.
        '''
        if condition not in self.color_icons:
            # Check for similarly-named conditions if no exact match found
            condition_lc = condition.lower()
            if 'cloudy' in condition_lc:
                if 'partly' in condition_lc:
                    condition = 'Partly Cloudy'
                else:
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

    @require(internet)
    def run(self):
        data = self.backend.weather_data()
        data['icon'], condition_color = self.get_color_data(data['condition'])
        color = condition_color if self.colorize else self.color

        self.output = {
            'full_text': formatp(self.format, **data).strip(),
            'color': color,
        }
