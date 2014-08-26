from . import IntervalModule
from .core.util import round_dict
import psutil

class NetworkTraffic(IntervalModule):
    """
    Network traffic per interface, i.e., packets/bytes sent/received per second.

    Requires the PyPI packages `psutil`.

    Available formatters:

    * `{interface}` — the configured network interface
    * `{bytes_sent}` — bytes sent per second (divided by divisor)
    * `{bytes_recv}` — bytes received per second (divided by divisor)
    * `{packets_sent}` — bytes sent per second (divided by divisor)
    * `{packets_recv}` — bytes received per second (divided by divisor)
    """

    interval = 1
    settings = (
        ("format", "format string"),
        ("interface", "network interface"),
        ("divisor", "divide all byte values by this value"),
        ("round_size", "defines number of digits in round"),
    )
 
    format = "{interface} \u2197{bytes_sent}kB/s \u2198{bytes_recv}kB/s"
    interface = "eth0"
    divisor = 1024
    round_size = None
 
    pnic = None
    def run(self):
        pnic_before = self.pnic
        self.pnic = psutil.net_io_counters(pernic=True)[self.interface]
        if not pnic_before: return
        cdict = {
            "bytes_sent": (self.pnic.bytes_sent - pnic_before.bytes_sent) / self.divisor,
            "bytes_recv": (self.pnic.bytes_recv - pnic_before.bytes_recv) / self.divisor,
            "packets_sent": self.pnic.packets_sent - pnic_before.packets_sent,
            "packets_recv": self.pnic.packets_recv - pnic_before.packets_recv,
        }
        round_dict(cdict, self.round_size)
        cdict["interface"] = self.interface
        self.output = {
            "full_text": self.format.format(**cdict),
            "instance": self.interface,
        }
