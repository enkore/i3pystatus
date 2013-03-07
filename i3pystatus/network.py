
from itertools import zip_longest

# PyPI: netifaces-py3
import netifaces

from i3pystatus import IntervalModule

class Network(IntervalModule):
    """
    Display network information about a interface.

    Requires the PyPI package `netifaces-py3`.

    Available formatters:
    * {inteface} same as setting
    * {name} same as setting
    * {v4} IPv4 address
    * {v4mask} subnet mask
    * {v6} IPv6 address
    * {v6mask} subnet mask
    * {mac} MAC of interface

    Not available addresses (i.e. no IPv6 connectivity) are replaced with empty strings.
    """

    settings = (
        ("interface", "Interface to obtain information for, i.e. eth0"),
        "format_up", "color_up",
        "format_down", "color_down",
        "name"
    )

    name = interface = "eth0"
    format_up = "{interface}: {v4}"
    format_down = "{interface}"
    color_up = "#00FF00"
    color_down = "#FF0000"

    def init(self):
        if self.interface not in netifaces.interfaces():
            raise RuntimeError("Unknown inteface {iface}!".format(iface=self.inteface))

        self.baseinfo = {
            "interface": self.interface,
            "name": self.name,
            "mac": netifaces.ifaddresses(self.interface)[netifaces.AF_PACKET][0]["addr"],
        }

    def run(self):
        info = netifaces.ifaddresses(self.interface)
        up = netifaces.AF_INET in info or netifaces.AF_INET6 in info
        fdict = dict(zip_longest(["v4", "v4mask", "v6", "v6mask"], [], fillvalue=""))
        fdict.update(self.baseinfo)

        if up:
            format = self.format_up
            color = self.color_up
            if netifaces.AF_INET in info:
                v4 = info[netifaces.AF_INET][0]
                fdict["v4"] = v4["addr"]
                fdict["v4mask"] = v4["netmask"]
            if netifaces.AF_INET6 in info:
                v6 = info[netifaces.AF_INET6][0]
                fdict["v6"] = v6["addr"]
                fdict["v6mask"] = v6["netmask"]
        else:
            format = self.format_down
            color = self.color_down

        self.output = {
            "full_text": format.format(**fdict),
            "color": color,
            "instance": self.interface
        }
