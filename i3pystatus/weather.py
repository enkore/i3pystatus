from i3pystatus import IntervalModule
import pywapi

class Weather(IntervalModule):

    """
    This module gets the weather from weather.com
    First, you need to get the code for the location from the website
    Available formatters:
        {temp}
    """

    interval = 20

    settings = (
        "location_code",
        "format",
    )
    required = ("location_code")

    location_code='PLXX0028'

    format = "{current_temp}°C"

    def run(self):
        current_temp = pywapi.get_weather_from_weather_com(self.location_code)['current_conditions']['temperature']
        self.output = {
            "full_text": self.format.format(current_temp=current_temp)
        }
        #print ( self.output )

#w=Weather()
#w.run()
    #def on_leftclick(self):
        #webbrowser.open_new_tab(self.instance.get_url())
