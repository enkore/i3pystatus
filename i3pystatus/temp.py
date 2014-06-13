import re
import glob

from i3pystatus import IntervalModule


class Temperature(IntervalModule):
    """
    Shows CPU temperature of Intel processors

    AMD is currently not supported as they can only report a relative temperature, which is pretty useless
    """

    settings = (
        ("format",
         "format string used for output. {temp} is the temperature in degrees celsius"),
        "color",
    )
    format = "{temp} °C"
    color = "#FFFFFF"

    def init(self):
        self.file = "/sys/class/thermal/thermal_zone0/temp"

    def run(self):
        with open(self.file, "r") as f:
            temp = float(f.read().strip()) / 1000

        self.output = {
            "full_text": self.format.format(temp=temp),
            "color": self.color,
        }
