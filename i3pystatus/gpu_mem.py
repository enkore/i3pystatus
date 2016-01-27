from i3pystatus import IntervalModule
from .utils import gpu


class GPUMemory(IntervalModule):
    """
    Shows GPU memory load

    Currently Nvidia only and nvidia-smi required

    .. rubric:: Available formatters

    * {avail_mem}
    * {percent_used_mem}
    * {used_mem}
    * {total_mem}
    """

    settings = (
        ("format", "format string used for output."),
        ("divisor", "divide all megabyte values by this value, default is 1 (megabytes)"),
        ("warn_percentage", "minimal percentage for warn state"),
        ("alert_percentage", "minimal percentage for alert state"),
        ("color", "standard color"),
        ("warn_color", "defines the color used wann warn percentage ist exceeded"),
        ("alert_color", "defines the color used when alert percentage is exceeded"),
        ("round_size", "defines number of digits in round"),

    )

    format = "{avail_mem} MiB"
    divisor = 1
    color = "#00FF00"
    warn_color = "#FFFF00"
    alert_color = "#FF0000"
    warn_percentage = 50
    alert_percentage = 80
    round_size = 1

    def run(self):
        info = gpu.query_nvidia_smi()

        if info.used_mem is not None and info.total_mem is not None:
            mem_percent = 100 * info.used_mem / info.total_mem
        else:
            mem_percent = None

        if mem_percent >= self.alert_percentage:
            color = self.alert_color
        elif mem_percent >= self.warn_percentage:
            color = self.warn_color
        else:
            color = self.color

        cdict = {
            "used_mem": info.used_mem / self.divisor,
            "avail_mem": info.avail_mem / self.divisor,
            "total_mem": info.total_mem / self.divisor,
            "percent_used_mem": mem_percent,
        }
        for key, value in cdict.items():
            if value is not None:
                cdict[key] = round(value, self.round_size)

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
