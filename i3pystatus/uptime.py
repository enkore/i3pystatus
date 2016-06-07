
from i3pystatus import IntervalModule, formatp


class Uptime(IntervalModule):
    """
    Outputs Uptime

    .. rubric:: Available formatters

    * `{days}` - uptime in days
    * `{hours}` - rest of uptime in hours
    * `{mins}` - rest of uptime in minutes
    * `{secs}` - rest of uptime in seconds
    * `{uptime}` - deprecated: equals '`{hours}:{mins}`'
    """

    settings = (
        ("format", "Format string"),
        ("color", "String color"),
        ("alert", "If you want the string to change color"),
        ("seconds_alert", "How many seconds necessary to start the alert"),
        ("color_alert", "Alert color"),
    )

    file = "/proc/uptime"
    format = "up {hours}:{mins}"
    color = "#ffffff"
    alert = False
    seconds_alert = 60 * 60 * 24 * 30  # 30 days
    color_alert = "#ff0000"

    def run(self):
        with open(self.file, "r") as f:
            seconds = int(float(f.read().split()[0]))

        days = seconds // (60 * 60 * 24)
        hours = seconds // (60 * 60)
        minutes = seconds // 60
        if "{days}" in self.format:
            hours = (seconds % (60 * 60 * 24)) // (60 * 60)
            minutes = (seconds % (60 * 60 * 24)) // 60
            seconds = (seconds % (60 * 60 * 24))
        if "{hours}" in self.format:
            minutes = (seconds % (60 * 60)) // 60
            seconds = (seconds % (60 * 60))
        if "{mins}" in self.format:
            seconds = seconds % 60

        fdict = {
            "days": days,
            "hours": hours,
            "mins": minutes,
            "secs": seconds,
            "uptime": "{}:{}".format(hours, minutes),
        }
        self.data = fdict
        if self.alert:
            if seconds > self.seconds_alert:
                self.color = self.color_alert
        self.output = {
            "full_text": formatp(self.format, **fdict),
            "color": self.color
        }
