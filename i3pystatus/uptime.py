
from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper


class Uptime(IntervalModule):
    """
    Outputs Uptime
    """

    settings = (
        ("format", "Format string"),
        ("color", "String color"),
        ("alert", "If you want the string to change color"),
        ("seconds_alert", "How many seconds necessary to start the alert"),
        ("color_alert", "Alert color"),
    )

    file = "/proc/uptime"
    format = "up {uptime}"
    color = "#ffffff"
    alert = False
    seconds_alert = 3600
    color_alert = "#ff0000"

    def run(self):
        with open(self.file, "r") as f:
            seconds = float(f.read().split()[0])
            fdict = {
                "uptime": TimeWrapper(seconds, "%h:%m"),
            }

        if self.alert:
            if seconds > self.seconds_alert:
                self.color = self.color_alert
        self.output = {
            "full_text": formatp(self.format, **fdict),
            "color": self.color
        }
