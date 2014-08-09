# -*- coding:utf-8 -*-

from i3pystatus.cpu_usage import CpuUsage
from i3pystatus.core.util import make_bar

class CpuUsageBar(CpuUsage):
    """
    Shows CPU usage as a bar (made with unicode box characters).
    The first output will be inacurate.

    Linux only

    Available formatters:

    * {usage_bar}       usage average of all cores
    * {usage_bar_cpu*}  usage of one specific core. replace "*"
    by core number starting at 0

    """

    format = "{usage_bar}"
    settings = (
        ("format", "format string"),
    )

    def run(self):
        cpu_usage = self.get_usage()

        cpu_usage_bar = {}

        for core, usage in cpu_usage.items():
            core = core.replace('usage', 'usage_bar')
            cpu_usage_bar[core] = make_bar(usage)

        cpu_usage.update(cpu_usage_bar)

        # for backward compatibility
        cpu_usage['usage_bar'] = cpu_usage['usage_bar_cpu']

        self.output = {
            "full_text": self.format.format_map(cpu_usage)
        }

