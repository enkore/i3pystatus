from i3pystatus import IntervalModule
from psutil import virtual_memory


class Mem(IntervalModule):
    """
    Shows memory load

    Available formatters:

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
    _round = 2

    settings = (
        ("format", "format string used for output."),
        ("divisor",
            "divide all byte values by this value, default 1024**2(mebibytes"),
        ("warn_percentage", "minimal percentage for warn state"),
        ("alert_percentage", "minimal percentage for alert state"),
        ("color", "standard color"),
        ("warn_color",
            "defines the color used wann warn percentage ist exceeded"),
        ("alert_color",
            "defines the color used when alert percentage is exceeded"),
        ("round", "round byte values to given length behind dot")
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

        self.output = {
            "full_text": self.format.format(
                used_mem=round(used / self.divisor, self._round),
                avail_mem=round(memory_usage.available / self.divisor,
                                self._round),
                total_mem=round(memory_usage.total / self.divisor, self._round),
                percent_used_mem=int(memory_usage.percent)),
            "color":color
        }
