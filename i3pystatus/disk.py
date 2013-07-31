import os

from i3pystatus import IntervalModule
from .core.util import round_dict

class Disk(IntervalModule):
    """
    Gets `{used}`, `{free}`, `{available}` and `{total}` amount of bytes on the given mounted filesystem.

    These values can also be expressed in percentages with the `{percentage_used}`, `{percentage_free}`
    and `{percentage_avail}` formats.
    """

    settings = (
        "format", "path",
        ("divisor", "divide all byte values by this value, commonly 1024**3 (gigabyte)"),
    )
    required = ("path",)
    color = "#FFFFFF"
    format = "{free}/{avail}"
    divisor = 1024**3

    def run(self):
        cdict = {}

        stat = os.statvfs(self.path)
        cdict = {
            "total": (stat.f_bsize * stat.f_blocks) / self.divisor,
            "free": (stat.f_bsize * stat.f_bfree) / self.divisor,
            "avail": (stat.f_bsize * stat.f_bavail) / self.divisor,
            "used": (stat.f_bsize * (stat.f_blocks - stat.f_bfree)) / self.divisor,
            "percentage_free": stat.f_bfree / stat.f_blocks * 100,
            "percentage_avail": stat.f_bavail / stat.f_blocks * 100,
            "percentage_used": (stat.f_blocks - stat.f_bfree) / stat.f_blocks * 100,
        }
        round_dict(cdict, 2)

        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.color
        }
