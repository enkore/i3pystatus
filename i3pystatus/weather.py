from i3pystatus import IntervalModule
import pywapi
from i3pystatus.core.util import internet, require


class Weather(IntervalModule):
    """
    This module gets the weather from weather.com using pywapi module
    First, you need to get the code for the location from the www.weather.com
    .. rubric:: Available formatters

    * {current_temp}
    * {current_wind}
    * {humidity}

    Requires pywapi from PyPI.
    """

    interval = 20

    settings = (
        "location_code",
        ("colorize", "Enable color with temperature and UTF-8 icons."),
        ("units", "Celsius (metric) or Fahrenheit (imperial)"),
        "format",
    )
    required = ("location_code",)

    units = "metric"
    format = "{current_temp}"
    colorize = False
    color_icons = {
        "Fair":  (u"\u2600", "#FFCC00"),
        "Cloudy": (u"\u2601", "#F8F8FF"),
        "Partly Cloudy": (u"\u2601", "#F8F8FF"),  # \u26c5 is not in many fonts
        "Rainy": (u"\u2614", "#CBD2C0"),
        "Sunny": (u"\u263C", "#FFFF00"),
        "Snow": (u"\u2603", "#FFFFFF"),
        "default": ("", None),
    }

    @require(internet)
    def run(self):
        result = pywapi.get_weather_from_weather_com(self.location_code, self.units)
        conditions = result["current_conditions"]
        temperature = conditions["temperature"]
        humidity = conditions["humidity"]
        wind = conditions["wind"]
        units = result["units"]
        color = None
        current_temp = "{t}°{d}".format(t=temperature, d=units["temperature"])
        current_wind = "{t} {s}{d}".format(t=wind["text"], s=wind["speed"], d=units["speed"])

        if self.colorize:
            icon, color = self.color_icons.get(conditions["text"],
                                               self.color_icons["default"])
            current_temp = "{t}°{d} {i}".format(t=temperature,
                                                d=units["temperature"],
                                                i=icon)
            color = color

        self.output = {
            "full_text": self.format.format(current_temp=current_temp, current_wind=current_wind, humidity=humidity),
            "color": color
        }
