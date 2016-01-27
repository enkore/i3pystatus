from i3pystatus.core.color import ColorRangeModule
from i3pystatus.cpu_usage import CpuUsage
from i3pystatus.core.util import make_graph


class CpuUsageGraph(CpuUsage, ColorRangeModule):
    """
     Shows CPU usage as a Unicode graph.
     The first output will be inacurate.

     Depends on the PyPI colour module - https://pypi.python.org/pypi/colour/0.0.5

     Linux only

     .. rubric:: Available formatters

     * `{cpu_graph}`  — graph of cpu usage.
     * `{usage}`      — usage average of all cores
     * `{usage_cpu*}` — usage of one specific core. replace "*" by core number starting at 0
     * `{usage_all}`  — usage of all cores separate. usess natsort when available(relevant for more than 10 cores)
     """

    settings = (
        ("cpu", "cpu to monitor, choices are 'usage_cpu' for all or 'usage_cpu*'. R"
                "eplace '*' by core number starting at 0."),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'"),
        ("graph_width", "Width of the cpu usage graph"),
        ("graph_style", "Graph style ('blocks', 'braille-fill', 'braille-peak', or 'braille-snake')"),
    )

    graph_width = 15
    graph_style = 'blocks'
    format = '{cpu_graph}'
    cpu = 'usage_cpu'

    def init(self):
        super().init()
        self.cpu_readings = self.graph_width * [0]
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, int(100))

    def run(self):
        format_options = self.get_usage()
        core_reading = format_options[self.cpu]

        self.cpu_readings.insert(0, core_reading)
        self.cpu_readings = self.cpu_readings[:self.graph_width]

        graph = make_graph(self.cpu_readings, 0.0, 100.0, self.graph_style)
        format_options.update({'cpu_graph': graph})

        color = self.get_gradient(core_reading, self.colors)
        self.data = format_options
        self.output = {
            "full_text": self.format.format_map(format_options),
            'color': color
        }
