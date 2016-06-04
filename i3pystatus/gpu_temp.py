from i3pystatus import IntervalModule
from .utils import gpu


class GPUTemperature(IntervalModule):
    """
    Shows GPU temperature

    Currently Nvidia only and nvidia-smi required

    .. rubric:: Available formatters

    * `{temp}`       — the temperature in integer degrees celsius
    """

    settings = (
        ("format", "format string used for output. {temp} is the temperature in integer degrees celsius"),
        ("display_if", "snippet that gets evaluated. if true, displays the module output"),
        "color",
        "alert_temp",
        "alert_color",
    )
    format = "{temp} °C"
    color = "#FFFFFF"
    alert_temp = 90
    alert_color = "#FF0000"
    display_if = True

    def run(self):
        temp = gpu.query_nvidia_smi().temp
        temp_alert = temp is None or temp >= self.alert_temp

        if eval(self.display_if):
            self.output = {
                "full_text": self.format.format(temp=temp),
                "color": self.color if not temp_alert else self.alert_color,
            }
