import os

from i3pystatus import IntervalModule
from .core.util import round_dict


class Disk(IntervalModule):
    """
    Gets ``{used}``, ``{free}``, ``{avail}`` and ``{total}`` amount of bytes on the given mounted filesystem.

    These values can also be expressed as percentages with the ``{percentage_used}``, ``{percentage_free}``
    and ``{percentage_avail}`` formats.
    """

    settings = (
        "format",
        "path",
        ("divisor", "divide all byte values by this value, default is 1024**3 (gigabyte)"),
        ("display_limit", "if more space is available than this limit the module is hidden"),
        ("critical_limit", "critical space limit (see critical_color)"),
        ("critical_color", "the critical color"),
        ("color", "the common color"),
        ("round_size", "precision, None for INT"),
        ("mounted_only", "display only if path is a valid mountpoint"),
        "format_not_mounted",
        "color_not_mounted"
    )
    required = ("path",)
    color = "#FFFFFF"
    color_not_mounted = "#FFFFFF"
    critical_color = "#FF0000"
    format = "{free}/{avail}"
    format_not_mounted = None
    divisor = 1024 ** 3
    display_limit = float('Inf')
    critical_limit = 0
    round_size = 2
    mounted_only = False

    def not_mounted(self):
        if self.mounted_only:
            self.output = {}
        else:
            self.output = {} if not self.format_not_mounted else {
                "full_text": self.format_not_mounted,
                "color": self.color_not_mounted,
            }

    def run(self):
        if os.path.isdir(self.path) and not os.path.ismount(self.path):
            if len(os.listdir(self.path)) == 0:
                self.not_mounted()
                return

        try:
            stat = os.statvfs(self.path)
        except Exception:
            self.not_mounted()
            return

        available = (stat.f_bsize * stat.f_bavail) / self.divisor

        if available > self.display_limit:
            self.output = {}
            return

        critical = available < self.critical_limit

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

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.critical_color if critical else self.color,
            "urgent": critical
        }
