from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require

from urllib.request import urlopen
import re
import xml.etree.ElementTree as ElementTree

WEATHER_COM_URL = 'http://wxdata.weather.com/wxdata/weather/local/%s?unit=%s&cc=*'

class Weather(IntervalModule):
    """
    This module gets the weather from weather.com.
    First, you need to get the code for the location from the www.weather.com

    .. rubric:: Available formatters

    * {current_temp}
    * {current_wind}
    * {humidity}

    """

    interval = 20

    settings = (
        "location_code",
        ("colorize", "Enable color with temperature and UTF-8 icons."),
        ("units", "Celsius (metric) or Fahrenheit (imperial)"),
        "format",
    )
    required = ("location_code",)

    location_code = None
    units = "metric"
    format = "{current_temp}"
    colorize = False
    color_icons = {
        "Fair": (u"\u2600", "#FFCC00"),
        "Cloudy": (u"\u2601", "#F8F8FF"),
        "Partly Cloudy": (u"\u2601", "#F8F8FF"),  # \u26c5 is not in many fonts
        "Rainy": (u"\u2614", "#CBD2C0"),
        "Sunny": (u"\u263C", "#FFFF00"),
        "Snow": (u"\u2603", "#FFFFFF"),
        "default": ("", None),
    }

    def fetch_weather(self):
        '''Fetches the current weather from wxdata.weather.com service.'''
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
        return dict(
            current_conditions=dict(
                text=doc.findtext('cc/t'),
                temperature=doc.findtext('cc/tmp'),
                humidity=doc.findtext('cc/hmid'),
                wind=dict(text=doc.findtext('cc/wind/t'), speed=doc.findtext('cc/wind/s'))
                ),
            units=dict(
                temperature=doc.findtext('head/ut'),
                speed=doc.findtext('head/us'),
                ),
            )

    @require(internet)
    def run(self):
        result = self.fetch_weather()
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
            "full_text": self.format.format(
                current_temp=current_temp,
                current_wind=current_wind,
                humidity=humidity,
                ),
            "color": color
        }
