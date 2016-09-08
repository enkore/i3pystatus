from collections import defaultdict
from string import Formatter
import re

from i3pystatus import IntervalModule
from i3pystatus.core.color import ColorRangeModule

try:
    from natsort import natsorted as sorted
except ImportError:
    pass


class CpuUsage(IntervalModule, ColorRangeModule):
    """
    Shows CPU usage.
    The first output will be inacurate.

    Linux only
    Requires the PyPI package 'colour'.

    .. rubric:: Available formatters

    * `{usage}`      — usage average of all cores
    * `{usage_cpu*}` — usage of one specific core. replace "*" by core number starting at 0
    * `{usage_all}`  — usage of all cores separate. usess natsort when available(relevant for more than 10 cores)

    """

    format = "{usage:02}%"
    format_all = "{core}:{usage:02}%"
    exclude_average = False
    interval = 1
    color = None
    dynamic_color = False
    upper_limit = 100
    settings = (
        ("format", "format string."),
        ("format_all", ("format string used for {usage_all} per core. "
                        "Available formaters are {core} and {usage}. ")),
        ("exclude_average", ("If True usage average of all cores will "
                             "not be in format_all.")),
        ("color", "HTML color code #RRGGBB"),
        ("dynamic_color", "Set color dynamically based on CPU usage. Note: this overrides color_up"),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'")
    )

    def init(self):
        self.prev_total = defaultdict(int)
        self.prev_busy = defaultdict(int)
        self.formatter = Formatter()

        self.key = re.findall('usage_cpu\d+', self.format)
        if len(self.key) == 1:
            self.key = self.key[0]
        else:
            self.key = 'usage_cpu'

        if not self.color:
            self.color = '#FFFFFF'

        if not self.dynamic_color:
            self.start_color = self.color
            self.end_color = self.color
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, int(self.upper_limit))

    def get_cpu_timings(self):
        """
        reads and parses /proc/stat
        returns dictionary with all available cores including global average
        """
        timings = {}
        with open('/proc/stat', 'r') as file_obj:
            for line in file_obj:
                if 'cpu' in line:
                    line = line.strip().split()
                    timings[line[0]] = [int(x) for x in line[1:]]

        return timings

    def calculate_usage(self, cpu, total, busy):
        """
        calculates usage
        """
        diff_total = total - self.prev_total[cpu]
        diff_busy = busy - self.prev_busy[cpu]

        self.prev_total[cpu] = total
        self.prev_busy[cpu] = busy

        if diff_total == 0:
            return 0
        else:
            return int(diff_busy / diff_total * 100)

    def gen_format_all(self, usage):
        """
        generates string for format all
        """
        format_string = " "
        core_strings = []
        for core, usage in usage.items():
            if core == 'usage_cpu' and self.exclude_average:
                continue
            elif core == 'usage':
                continue

            core = core.replace('usage_', '')
            string = self.formatter.format(format_string=self.format_all,
                                           core=core,
                                           usage=usage)
            core_strings.append(string)

        core_strings = sorted(core_strings)

        return format_string.join(core_strings)

    def get_usage(self):
        """
        parses /proc/stat and calcualtes total and busy time
        (more specific USER_HZ see man 5 proc for further informations )
        """
        usage = {}

        for cpu, timings in self.get_cpu_timings().items():
            cpu_total = sum(timings)
            del timings[3:5]
            cpu_busy = sum(timings)
            cpu_usage = self.calculate_usage(cpu, cpu_total, cpu_busy)

            usage['usage_' + cpu] = cpu_usage

        # for backward compatibility
        usage['usage'] = usage['usage_cpu']

        return usage

    def run(self):
        usage = self.get_usage()
        usage['usage_all'] = self.gen_format_all(usage)

        color = self.get_gradient(usage[self.key], self.colors, int(self.upper_limit))

        self.data = usage
        self.output = {
            "full_text": self.format.format_map(usage),
            "color": color
        }
