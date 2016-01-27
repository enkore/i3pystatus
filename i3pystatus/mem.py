from i3pystatus import IntervalModule
from psutil import virtual_memory
from .core.util import round_dict


class Mem(IntervalModule):
    """
    Shows memory load

    .. rubric:: Available formatters

    * {avail_mem}
    * {percent_used_mem}
    * {used_mem}
    * {total_mem}

    Requires psutil (from PyPI)
    """

    format = "{avail_mem} MiB"
    divisor = 1024 ** 2
    color = "#00FF00"
    warn_color = "#FFFF00"
    alert_color = "#FF0000"
    warn_percentage = 50
    alert_percentage = 80
    round_size = 1

    settings = (
        ("format", "format string used for output."),
        ("divisor",
         "divide all byte values by this value, default is 1024**2 (megabytes)"),
        ("warn_percentage", "minimal percentage for warn state"),
        ("alert_percentage", "minimal percentage for alert state"),
        ("color", "standard color"),
        ("warn_color",
         "defines the color used wann warn percentage ist exceeded"),
        ("alert_color",
         "defines the color used when alert percentage is exceeded"),
        ("round_size", "defines number of digits in round"),

    )

    def run(self):
        memory_usage = virtual_memory()
        used = memory_usage.used - memory_usage.cached - memory_usage.buffers

        if memory_usage.percent >= self.alert_percentage:
            color = self.alert_color

        elif memory_usage.percent >= self.warn_percentage:
            color = self.warn_color
        else:
            color = self.color

        cdict = {
            "used_mem": used / self.divisor,
            "avail_mem": memory_usage.available / self.divisor,
            "total_mem": memory_usage.total / self.divisor,
            "percent_used_mem": memory_usage.percent,
        }
        round_dict(cdict, self.round_size)

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
