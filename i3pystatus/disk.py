import os
import subprocess

from i3pystatus import IntervalModule
from .core.util import round_dict


class Disk(IntervalModule):
    """
    Gets ``{used}``, ``{free}``, ``{available}`` and ``{total}`` amount of bytes on the given mounted filesystem.

    These values can also be expressed as percentages with the ``{percentage_used}``, ``{percentage_free}``
    and ``{percentage_avail}`` formats.
    """

    settings = (
        "format", "path",
        ("divisor", "divide all byte values by this value, default is 1024**3 (gigabyte)"),
        ("display_limit", "if more space is available than this limit the module is hidden"),
        ("critical_limit", "critical space limit (see critical_color)"),
        ("critical_color", "the critical color"),
        ("color", "the common color"),
        ("round_size", "precision, None for INT"),
    )
    required = ("path",)
    color = "#FFFFFF"
    critical_color = "#FF0000"
    format = "{free}/{avail}"
    divisor = 1024 ** 3
    display_limit = float('Inf')
    critical_limit = 0
    round_size = 2

    def run(self):
        stat = os.statvfs(self.path)
        available = (stat.f_bsize * stat.f_bavail) / self.divisor

        if available > self.display_limit:
            self.output = {}
            return

        cdict = {
            "total": (stat.f_bsize * stat.f_blocks) / self.divisor,
            "free": (stat.f_bsize * stat.f_bfree) / self.divisor,
            "avail": available,
            "used": (stat.f_bsize * (stat.f_blocks - stat.f_bfree)) / self.divisor,
            "percentage_free": stat.f_bfree / stat.f_blocks * 100,
            "percentage_avail": stat.f_bavail / stat.f_blocks * 100,
            "percentage_used": (stat.f_blocks - stat.f_bfree) / stat.f_blocks * 100,
        }
        round_dict(cdict, self.round_size)

        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.color if available > self.critical_limit else self.critical_color,
            "urgent": available > self.critical_limit
        }

    def on_leftclick(self):
        subprocess.Popen(["thunar", self.path ])
