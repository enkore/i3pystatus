from collections import defaultdict
from string import Formatter

from i3pystatus import IntervalModule

try:
    from natsort import natsorted as sorted
except ImportError:
    pass


class CpuUsage(IntervalModule):
    """
    Shows CPU usage.
    The first output will be inacurate.

    Linux only

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
    settings = (
        ("format", "format string."),
        ("format_all", ("format string used for {usage_all} per core. "
                        "Available formaters are {core} and {usage}. ")),
        ("exclude_average", ("If True usage average of all cores will "
                             "not be in format_all.")),
        ("color", "HTML color code #RRGGBB")
    )

    def init(self):
        self.prev_total = defaultdict(int)
        self.prev_busy = defaultdict(int)
        self.formatter = Formatter()

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

        self.data = usage
        self.output = {
            "full_text": self.format.format_map(usage),
            "color": self.color
        }
