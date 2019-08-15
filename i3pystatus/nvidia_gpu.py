from i3pystatus import IntervalModule
from .utils import gpu


class NvidiaGPU(IntervalModule):
    """
    Shows Nvidia GPU information

    Nvidia-smi required

    .. rubric:: Available formatters

    * {usage} gpu usage in percent
    * {avail_mem} available memory
    * {used_mem} used memory
    * {total_mem} total memory
    * {percent_used_mem} used_mem / total_mem
    * {temp} the temperature in degrees celsius
    """

    settings = (
        ("format", "format string used for output."),
        ("format_no_gpu_found", "Text to display when no GPUs are found. In such a case no formatters are available."),
        ("divisor", "All memory values are divided by this. Default is 1 which outputs megabytes."),
        ("coloring_based_on", "What data to base the coloring on. Allowed values are 'usage', 'mem', 'temp'"),
        ("warn_value", "minimal value for warn state (value of the data type chosen with 'coloring_based_on' setting)"),
        ("alert_value", "minimal value for alert state (value of the data type chosen with 'coloring_based_on' setting)"),
        ("color", "standard color"),
        ("warn_color", "Defines the color used when warn value is exceeded."),
        ("alert_color", "Defines the color used when alert value is exceeded."),
        ("color_no_gpu_found", "Color to use for text when no GPUs are found."),
        ("round_size", "Defines number of digits in round. Applied to all values."),
        ("gpu_number", "GPU number, in case of multiple GPUs"),
    )

    format = "{usage}% {temp}°C"
    format_no_gpu_found = "No GPUs found"
    divisor = 1
    coloring_based_on = "usage"
    color = "#00FF00"
    warn_color = "#FFFF00"
    alert_color = "#FF0000"
    warn_value = 50
    alert_value = 80
    color_no_gpu_found = "#FF0000"
    round_size = 1
    gpu_number = 0

    def run(self):
        try:
            info = gpu.query_nvidia_smi(self.gpu_number)
        except gpu.GPUNotFoundError:
            self.output = {
                "full_text": self.format_no_gpu_found,
                "color": self.color_no_gpu_found
            }
            return

        # Usage
        gpu_percent = info.usage_gpu

        # Mem
        if info.used_mem is not None and info.total_mem is not None:
            mem_percent = 100 * info.used_mem / info.total_mem
        else:
            mem_percent = None

        # Temp
        temp = info.temp

        # Color
        if self.coloring_based_on == "usage":
            if gpu_percent >= self.alert_value:
                color = self.alert_color
            elif gpu_percent >= self.warn_value:
                color = self.warn_color
            else:
                color = self.color
        elif self.coloring_based_on == "mem":
            if mem_percent >= self.alert_value:
                color = self.alert_color
            elif mem_percent >= self.warn_value:
                color = self.warn_color
            else:
                color = self.color
        elif self.coloring_based_on == "temp":
            if temp >= self.alert_value:
                color = self.alert_color
            elif temp >= self.warn_value:
                color = self.warn_color
            else:
                color = self.color


        cdict = {
            "usage": gpu_percent,
            "used_mem": info.used_mem / self.divisor,
            "avail_mem": info.avail_mem / self.divisor,
            "total_mem": info.total_mem / self.divisor,
            "percent_used_mem": mem_percent,
            "temp": temp,
        }

        for key, value in cdict.items():
            if value is not None:
                cdict[key] = round(value, self.round_size)

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
