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
         "format string used for output. {temp} is the temperature in degrees celsius, {critical} and {high} are the trip point temps."),
        "color", "color_critical", "high_factor"
    )
    format = "{temp} °C"
    high_factor = 0.7
    color = "#FFFFFF"
    color_high = "#FFFF00"
    color_critical = "#FF0000"
    base_path = "/sys/devices/platform/coretemp.0"

    def init(self):
        input = glob.glob(
            "{base_path}/temp*_input".format(base_path=self.base_path))[0]
        self.input = re.search("temp([0-9]+)_input", input).group(1)
        self.base_path = "{base_path}/temp{input}_".format(
            base_path=self.base_path, input=self.input)

        with open("{base_path}crit".format(base_path=self.base_path), "r") as f:
            self.critical = float(f.read().strip()) / 1000
            self.high = self.critical * self.high_factor

    def run(self):
        with open("{base_path}input".format(base_path=self.base_path), "r") as f:
            temp = float(f.read().strip()) / 1000

        urgent = False
        color = self.color
        if temp >= self.critical:
            urgent = True
            color = self.color_critical
        elif temp >= self.high:
            urgent = True
            color = self.color_high

        self.output = {
            "full_text": self.format.format(temp=temp, critical=self.critical, high=self.high),
            "urgent": urgent,
            "color": color,
        }
