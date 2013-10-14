from i3pystatus import IntervalModule
import pywapi

class Weather(IntervalModule):

    """
    This module gets the weather from weather.com using pywapi module
    First, you need to get the code for the location from the www.weather.com
    Available formatters:
        {current_temp}
        {humidity}
    """

    interval = 20

    settings = (
        "location_code",
        "units",
        "format",
    )
    #required = ("location_code")
    format = "{current_temp}"

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
