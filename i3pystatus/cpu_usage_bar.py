# -*- coding:utf-8 -*-

from i3pystatus import IntervalModule
from i3pystatus.core.util import make_bar

class CpuUsageBar(IntervalModule):
    """
    Shows CPU usage as a bar (made with unicode box characters).
    The first output will be inacurate
    Linux only

    Available formatters:

    * {usage_bar}

    """

    format = "{usage_bar}"
    settings = (
        ("format", "format string"),
    )

    def init(self):
        self.prev_idle = 0
        self.prev_busy = 0
        self.interval = 1

    def get_usage(self):
        """
        parses /proc/stat and calcualtes total and busy time
        (more specific USER_HZ see man 5 proc for further informations )
        """
        with open('/proc/stat', 'r') as file_obj:
            stats = file_obj.readline().strip().split()

        cpu_timings = [int(x) for x in stats[1:]]
        cpu_total = sum(cpu_timings)
        del cpu_timings[3:5]
        cpu_busy = sum(cpu_timings)

        return cpu_total, cpu_busy

    def run(self):
        cpu_total, cpu_busy = self.get_usage()

        diff_cpu_total = cpu_total - self.prev_idle
        diff_cpu_busy = cpu_busy - self.prev_busy

        self.prev_idle = cpu_total
        self.prev_busy = cpu_busy

        cpu_busy_percentage = diff_cpu_busy / diff_cpu_total * 100
        cpu_busy_bar = make_bar(cpu_busy_percentage)

        self.output = {
            "full_text": self.format.format(
                usage_bar=cpu_busy_bar
            )
        }

