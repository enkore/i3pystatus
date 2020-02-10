from i3pystatus.core.color import ColorRangeModule
from i3pystatus.cpu_usage import CpuUsage
from i3pystatus.core.util import make_bar, make_vertical_bar


class CpuUsageBar(CpuUsage, ColorRangeModule):
    """
    Shows CPU usage as a bar (made with unicode box characters).
    The first output will be inacurate.

    Linux only

    Requires the PyPI package `colour`.

    .. rubric:: Available formatters

    * `{usage_bar}`      — usage average of all cores
    * `{usage_bar_cpu*}` — usage of one specific core. replace "*" by core number starting at 0
    """

    format = "{usage_bar}"
    bar_type = 'horizontal'
    cpu = 'usage_cpu'

    settings = (
        ("format", "format string"),
        ("bar_type", "whether the bar should be vertical or horizontal. "
                     "Allowed values: `vertical` or `horizontal`"),
        ("cpu", "cpu to base the colors on. Choices are 'usage_cpu' for all or 'usage_cpu*'."
                " Replace '*' by core number starting at 0."),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'"),
        ("dynamic_color", "Use dynamic color"),
    )

    def init(self):
        super().init()
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, 100)

    def run(self):
        cpu_usage = self.get_usage()

        cpu_usage_bar = {}

        for core, usage in cpu_usage.items():
            core = core.replace('usage', 'usage_bar')
            if self.bar_type == 'horizontal':
                cpu_usage_bar[core] = make_bar(usage)
            elif self.bar_type == 'vertical':
                cpu_usage_bar[core] = make_vertical_bar(usage)
            else:
                raise Exception("bar_type must be 'horizontal' or 'vertical'!")

        cpu_usage.update(cpu_usage_bar)

        # for backward compatibility
        cpu_usage['usage_bar'] = cpu_usage['usage_bar_cpu']

        self.data = cpu_usage
        self.output = {
            "full_text": self.format.format_map(cpu_usage),
            'color': self.get_gradient(cpu_usage[self.cpu], self.colors, 100)
        }
