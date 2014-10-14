from itertools import zip_longest
import subprocess

import netifaces

from i3pystatus import IntervalModule

# Reminder: if we raise minimum Python version to 3.3, use ipaddress module


def count_bits(integer):
    bits = 0
    while (integer):
        integer &= integer - 1
        bits += 1
    return bits


def v6_to_int(v6):
    return int(v6.replace(":", ""), 16)


def prefix6(mask):
    return count_bits(v6_to_int(mask))


def cidr6(addr, mask):
    return "{addr}/{bits}".format(addr=addr, bits=prefix6(mask))


def v4_to_int(v4):
    sum = 0
    mul = 1
    for part in reversed(v4.split(".")):
        sum += int(part) * mul
        mul *= 2 ** 8
    return sum


def prefix4(mask):
    return count_bits(v4_to_int(mask))


def cidr4(addr, mask):
    return "{addr}/{bits}".format(addr=addr, bits=prefix4(mask))


def get_bonded_slaves():
    try:
        with open("/sys/class/net/bonding_masters") as f:
            masters = f.read().split()
    except FileNotFoundError:
        return {}
    slaves = {}
    for master in masters:
        with open("/sys/class/net/{}/bonding/slaves".format(master)) as f:
            for slave in f.read().split():
                slaves[slave] = master
    return slaves


def sysfs_interface_up(interface, unknown_up=False):
    try:
        with open("/sys/class/net/{}/operstate".format(interface)) as f:
            status = f.read().strip()
    except FileNotFoundError:
        raise RuntimeError("Unknown interface {iface}!".format(iface=interface))
    return status == "up" or unknown_up and status == "unknown"


class Network(IntervalModule):
    """
    Display network information about a interface.

    Requires the PyPI package `netifaces`.

    .. rubric:: Available formatters

    * `{interface}` — same as setting
    * `{name}` — same as setting
    * `{v4}` — IPv4 address
    * `{v4mask}` — subnet mask
    * `{v4cidr}` — IPv4 address in cidr notation (i.e. 192.168.2.204/24)
    * `{v6}` — IPv6 address
    * `{v6mask}` — subnet mask
    * `{v6cidr}` — IPv6 address in cidr notation
    * `{mac}` — MAC of interface

    Not available addresses (i.e. no IPv6 connectivity) are replaced with empty strings.
    """

    settings = (
        ("interface", "Interface to obtain information for"),
        "format_up", "color_up",
        "format_down", "color_down",
        ("detached_down", "If the interface doesn't exist, display it as if it were down"),
        ("unknown_up", "If the interface is in unknown state, display it as if it were up"),
        "name",
    )

    name = interface = "eth0"
    format_up = "{interface}: {v4}"
    format_down = "{interface}"
    color_up = "#00FF00"
    color_down = "#FF0000"
    detached_down = True
    unknown_up = False

    def init(self):
        if self.interface not in netifaces.interfaces() and not self.detached_down:
            raise RuntimeError(
                "Unknown interface {iface}!".format(iface=self.interface))

    def collect(self):
        if self.interface not in netifaces.interfaces() and self.detached_down:
            self.format = self.format_down
            color = self.color_down
            return self.color_down, self.format_down, {"interface": self.interface, "name": self.name}, False

        info = netifaces.ifaddresses(self.interface)
        slaves = get_bonded_slaves()
        try:
            master = slaves[self.interface]
        except KeyError:
            pass
        else:
            if sysfs_interface_up(self.interface, self.unknown_up):
                master_info = netifaces.ifaddresses(master)
                for af in (netifaces.AF_INET, netifaces.AF_INET6):
                    try:
                        info[af] = master_info[af]
                    except KeyError:
                        pass
        up = sysfs_interface_up(self.interface, self.unknown_up)
        fdict = dict(
            zip_longest(["v4", "v4mask", "v4cidr", "v6", "v6mask", "v6cidr"], [], fillvalue=""))

        try:
            mac = info[netifaces.AF_PACKET][0]["addr"]
        except KeyError:
            mac = "NONE"
        fdict.update({
            "interface": self.interface,
            "name": self.name,
            "mac": mac,
        })

        if up:
            format = self.format_up
            color = self.color_up
            if netifaces.AF_INET in info:
                v4 = info[netifaces.AF_INET][0]
                fdict["v4"] = v4["addr"]
                fdict["v4mask"] = v4["netmask"]
                fdict["v4cidr"] = cidr4(v4["addr"], v4["netmask"])
            if netifaces.AF_INET6 in info:
                for v6 in info[netifaces.AF_INET6]:
                    fdict["v6"] = v6["addr"]
                    fdict["v6mask"] = v6["netmask"]
                    fdict["v6cidr"] = cidr6(v6["addr"], v6["netmask"])
                    if not v6["addr"].startswith("fe80::"):  # prefer non link-local addresses
                        break
        else:
            format = self.format_down
            color = self.color_down

        return color, format, fdict, up

    def run(self):
        color, format, fdict, up = self.collect()

        self.output = {
            "full_text": format.format(**fdict),
            "color": color,
            "instance": self.interface
        }

    def on_leftclick(self):
        subprocess.Popen(["nm-connection-editor"])
