from . import IntervalModule
from .core.util import round_dict
import psutil


class NetworkTraffic(IntervalModule):
    """
    Network traffic per interface, i.e., packets/bytes sent/received per second.

    Requires the PyPI packages `psutil`.

    .. rubric:: Available formatters

    * `{interface}` — the configured network interface
    * `{bytes_sent}` — bytes sent per second (divided by divisor)
    * `{bytes_recv}` — bytes received per second (divided by divisor)
    * `{packets_sent}` — bytes sent per second (divided by divisor)
    * `{packets_recv}` — bytes received per second (divided by divisor)
    """

    interval = 1
    settings = (
        ("format", "format string"),
        ("format_down", "format string if the interface is down (unless hide_down is set)"),
        ("hide_down", "whether to not display a interface which is down"),
        ("interface", "network interface"),
        ("divisor", "divide all byte values by this value"),
        ("round_size", "defines number of digits in round"),
    )

    format = "{interface} \u2197{bytes_sent}kB/s \u2198{bytes_recv}kB/s"
    format_down = "{interface} \u2013"
    hide_down = True
    interface = "eth0"
    divisor = 1024
    round_size = None

    pnic = None
    pnic_before = None

    def update_counters(self):
        self.pnic_before = self.pnic
        counters = psutil.net_io_counters(pernic=True)
        self.pnic = counters[self.interface] if self.interface in counters else None

    def get_bytes_sent(self):
        return (self.pnic.bytes_sent - self.pnic_before.bytes_sent) / self.divisor

    def get_bytes_received(self):
        return (self.pnic.bytes_recv - self.pnic_before.bytes_recv) / self.divisor

    def get_packets_sent(self):
        return self.pnic.packets_sent - self.pnic_before.packets_sent

    def get_packets_received(self):
        return self.pnic.packets_recv - self.pnic_before.packets_recv

    def sysfs_interface_up(self):
        try:
            sysfs = "/sys/class/net/{}/operstate".format(self.interface)
            with open(sysfs) as operstate:
                status = operstate.read().strip()
            return status == "up" or status == "unknown"
        except FileNotFoundError:
            return False

    def run(self):
        self.update_counters()
        if self.sysfs_interface_up():
            if not self.pnic_before:
                return
            cdict = {
                "bytes_sent": self.get_bytes_sent(),
                "bytes_recv": self.get_bytes_received(),
                "packets_sent": self.get_packets_sent(),
                "packets_recv": self.get_packets_received(),
            }
            round_dict(cdict, self.round_size)
            cdict["interface"] = self.interface
            self.output = {
                "full_text": self.format.format(**cdict),
                "instance": self.interface,
            }
        elif self.hide_down:
            self.output = None
            return
        else:
            cdict = {
                "interface": self.interface,
            }
            self.output = {
                "full_text": self.format_down.format(**cdict),
                "instance": self.interface,
            }
