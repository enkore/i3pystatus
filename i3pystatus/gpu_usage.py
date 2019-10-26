from i3pystatus import IntervalModule
from .utils import gpu


class GPUUsage(IntervalModule):
    """
    Shows GPU load in percent

    Currently Nvidia only and nvidia-smi required

    .. rubric:: Available formatters

    * {usage}
    """

    settings = (
        ("format", "format string used for output."),
        ("warn_percentage", "minimal percentage for warn state"),
        ("alert_percentage", "minimal percentage for alert state"),
        ("color", "standard color"),
        ("warn_color", "defines the color used when warn percentage is exceeded"),
        ("alert_color", "defines the color used when alert percentage is exceeded"),
        ("gpu_number", "set the gpu number when you have several GPU"),
    )

    format = "{usage}%"
    divisor = 1
    color = "#00FF00"
    warn_color = "#FFFF00"
    alert_color = "#FF0000"
    warn_percentage = 50
    alert_percentage = 80
    round_size = 1
    gpu_number = 0

    def run(self):
        info = gpu.query_nvidia_smi(self.gpu_number)

        gpu_percent = info.usage_gpu

        if gpu_percent >= self.alert_percentage:
            color = self.alert_color
        elif gpu_percent >= self.warn_percentage:
            color = self.warn_color
        else:
            color = self.color

        cdict = {
            "usage": gpu_percent,
        }

        for key, value in cdict.items():
            if value is not None:
                cdict[key] = value

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
