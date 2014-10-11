# -*- coding: utf-8 -*-
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.network_traffic import NetworkTraffic
from i3pystatus.core.util import make_graph


class NetworkGraph(NetworkTraffic, ColorRangeModule):
    """
    Shows Network activity as a Unicode graph

    Linux only

    Available formatters:

    {kbs}               Float representing kb\s
    {network_graph}     Unicode network graph

    """
    settings = (
        ("format", "format string"),
        ("graph_width", "Width of the graph"),
        ("upper_limit", "Expected max kb/s. This value controls how the graph is drawn and in what color"),
        ("graph_type", "Whether to draw the graph for input or output. "
                       "Allowed values 'input' or 'output'"),
        ("divisor", "divide all byte values by this value"),
        ("interface", "Interface to watch, eg 'eth0'"),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'")
    )

    format = "{network_graph}{kbs}KB/s"
    graph_type = 'input'

    interval = 1
    graph_width = 15
    upper_limit = 150.0

    def init(self):
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, int(self.upper_limit))
        self.kbs_arr = [0.0] * self.graph_width

    def run(self):
        self.update_counters()
        if not self.pnic_before:
            return

        if self.graph_type == 'input':
            kbs = self.get_bytes_received()
        elif self.graph_type == 'output':
            kbs = self.get_bytes_sent()
        else:
            raise Exception("graph_type must be either 'input' or 'output'!")

        # Cycle array by inserting at the start and chopping off the last element
        self.kbs_arr.insert(0, kbs)
        self.kbs_arr = self.kbs_arr[:self.graph_width]

        color = self.get_gradient(kbs, self.colors, self.upper_limit)
        network_graph = make_graph(self.kbs_arr, self.upper_limit)

        self.output = {
            "full_text": self.format.format(
                network_graph=network_graph,
                kbs="{0:.1f}".format(round(kbs, 2)).rjust(6)
            ),
            'color': color,
        }
