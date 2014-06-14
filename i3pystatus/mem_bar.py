from i3pystatus import IntervalModule
from psutil import virtual_memory
from i3pystatus.core.util import make_bar


class MemBar(IntervalModule):
    """
    Shows memory load as a bar.

    Available formatters:
    * {used_mem_bar}

    Requires psutil (from PyPI)
    """

    format = "{used_mem_bar}"
    color = "#00FF00"
    warn_color = "#FFFF00"
    alert_color = "#FF0000"
    warn_percentage = 50
    alert_percentage = 80

    settings = (
        ("format", "format string used for output."),
        ("warn_percentage", "minimal percentage for warn state"),
        ("alert_percentage", "minimal percentage for alert state"),
        ("color", "standard color"),
        ("warn_color",
         "defines the color used wann warn percentage ist exceeded"),
        ("alert_color",
         "defines the color used when alert percentage is exceeded"),
    )

    def run(self):
        memory_usage = virtual_memory()

        if memory_usage.percent >= self.alert_percentage:
            color = self.alert_color

        elif memory_usage.percent >= self.warn_percentage:
            color = self.warn_color
        else:
            color = self.color

        self.output = {
            "full_text": self.format.format(
                used_mem_bar=make_bar(memory_usage.percent)),
            "color": color
        }
