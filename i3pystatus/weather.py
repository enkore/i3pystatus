from i3pystatus import IntervalModule
import pywapi
from i3pystatus.core.util import internet, require


class Weather(IntervalModule):

    """
    This module gets the weather from weather.com using pywapi module
    First, you need to get the code for the location from the www.weather.com
    Available formatters:

    * {current_temp}
    * {humidity}

    Requires pywapi from PyPI.
    """

    interval = 20

    settings = (
        "location_code",
        ("units", "Celsius (metric) or Fahrenheit (imperial)"),
        "format",
    )
    required = ("location_code",)

    units = "metric"
    format = "{current_temp}"

    @require(internet)
    def run(self):
        result = pywapi.get_weather_from_weather_com(self.location_code, self.units)
        conditions = result['current_conditions']
        temperature = conditions['temperature']
        humidity = conditions['humidity']
        units = result['units']
        current_temp = '{t}°{d}'.format(t=temperature, d=units['temperature'])
        self.output = {
            "full_text": self.format.format(current_temp=current_temp, humidity=humidity)
        }
