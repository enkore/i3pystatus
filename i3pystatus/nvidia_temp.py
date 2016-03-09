import subprocess
from i3pystatus import IntervalModule


class NvidiaTemperature(IntervalModule):
    """
    Shows nVidia GPU temperature
    """

    settings = (
        ("format",
         "format string used for output. {temp} is the temperature in ",
         "degrees celsius"),
        "color",
        "alert_temp",
        "alert_color",
        "interval"
    )
    format = "{temp} °C"
    color = "#FFFFFF"
    alert_temp = 90
    alert_color = "#FF0000"
    interval = 5

    def run(self):
        # call nvidia-smi and strip newlines
        ret = subprocess.run(
            ['nvidia-smi',
             '--query-gpu=temperature.gpu',
             '--format=csv,noheader'],
            stdout=subprocess.PIPE).stdout.strip()
        # convirt string to int
        temp = int(ret)

        self.output = {
            "full_text": self.format.format(temp=temp),
            "color": self.color if temp < self.alert_temp else self.alert_color
        }
