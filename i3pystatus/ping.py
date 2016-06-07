import subprocess

from i3pystatus import IntervalModule


class Ping(IntervalModule):
    """
    This module display the ping value between your computer and a host.

    ``switch_state`` callback can disable the Ping when desired.
    ``host`` propertie can be changed for set a specific host.

    .. rubric:: Available formatters

    * {ping} the ping value in milliseconds.
    """

    interval = 5

    settings = (
        "color",
        "format",
        ("color_disabled", "color when disabled"),
        ("color_down", "color when ping fail"),
        ("format_disabled", "format string when disabled"),
        ("format_down", "format string when ping fail"),
        ("host", "host to ping")
    )

    color = "#FFFFFF"
    color_down = "#FF0000"
    color_disabled = None

    disabled = False

    format = "{ping} ms"
    format_down = "down"
    format_disabled = None

    host = "8.8.8.8"

    on_leftclick = "switch_state"

    def init(self):
        if not self.color_down:
            self.color_down = self.color
        if not self.format_disabled:
            self.format_disabled = self.format_down
        if not self.color_disabled:
            self.color_disabled = self.color_down

    def switch_state(self):
        self.disabled = not self.disabled

    def ping_host(self):
        p = subprocess.Popen(["ping", "-c1", "-w%d" % self.interval,
                              self.host], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
        out, _ = p.communicate()
        if p.returncode == 0:
            return float(out.decode().split("\n")[1]
                         .split("time=")[1].split()[0])
        else:
            return None

    def run(self):
        if self.disabled:
            self.output = {
                "full_text": self.format_disabled,
                "color": self.color_disabled
            }
            return

        ping = self.ping_host()
        if not ping:
            self.output = {
                "full_text": self.format_down,
                "color": self.color_down
            }
            return

        self.output = {
            "full_text": self.format.format(ping=ping),
            "color": self.color
        }
