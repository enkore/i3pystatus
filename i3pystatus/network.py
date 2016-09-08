import netifaces

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.core.util import make_graph, round_dict, make_bar


def count_bits(integer):
    bits = 0
    while integer:
        integer &= integer - 1
        bits += 1
    return bits


def cidr6(addr, bits):
    return "{addr}/{bits}".format(addr=addr, bits=bits)


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
        # Interface doesn't exist
        return False

    return status == "up" or unknown_up and status == "unknown"


class NetworkInfo:
    """
    Retrieve network information.
    """

    def __init__(self, interface, ignore_interfaces, detached_down, unknown_up, get_wifi_info=False):
        if interface not in netifaces.interfaces() and not detached_down:
            raise RuntimeError(
                "Unknown interface {iface}!".format(iface=interface))

        self.ignore_interfaces = ignore_interfaces
        self.detached_down = detached_down
        self.unknown_up = unknown_up
        self.get_wifi_info = get_wifi_info

    def get_info(self, interface):
        format_dict = dict(v4="", v4mask="", v4cidr="", v6="", v6mask="", v6cidr="")
        iface_up = sysfs_interface_up(interface, self.unknown_up)
        if not iface_up:
            return format_dict

        network_info = netifaces.ifaddresses(interface)
        slaves = get_bonded_slaves()
        try:
            master = slaves[interface]
        except KeyError:
            pass
        else:
            if sysfs_interface_up(interface, self.unknown_up):
                master_info = netifaces.ifaddresses(master)
                for af in (netifaces.AF_INET, netifaces.AF_INET6):
                    try:
                        network_info[af] = master_info[af]
                    except KeyError:
                        pass

        try:
            mac = network_info[netifaces.AF_PACKET][0]["addr"]
        except KeyError:
            mac = "NONE"
        format_dict['mac'] = mac

        if iface_up:
            format_dict.update(self.extract_network_info(network_info))
            format_dict.update(self.extract_wireless_info(interface))

        return format_dict

    @staticmethod
    def extract_network_info(network_info):
        info = dict()
        if netifaces.AF_INET in network_info:
            v4 = network_info[netifaces.AF_INET][0]
            info["v4"] = v4["addr"]
            info["v4mask"] = v4["netmask"]
            info["v4cidr"] = cidr4(v4["addr"], v4["netmask"])
        if netifaces.AF_INET6 in network_info:
            for v6 in network_info[netifaces.AF_INET6]:
                info["v6"] = v6["addr"]
                mask, bits = v6["netmask"].split("/")
                info["v6mask"] = mask
                info["v6cidr"] = cidr6(v6["addr"], bits)
                if not v6["addr"].startswith("fe80::"):  # prefer non link-local addresses
                    break
        return info

    def extract_wireless_info(self, interface):
        info = dict(essid="", freq="", quality=0.0, quality_bar="")

        # Just return empty values if we're not using any Wifi functionality
        if not self.get_wifi_info:
            return info

        import basiciw

        try:
            iwi = basiciw.iwinfo(interface)
        except Exception:
            # Not a wireless interface
            return info

        info["essid"] = iwi["essid"]
        info["freq"] = iwi["freq"]
        quality = iwi["quality"]
        if quality["quality_max"] > 0:
            info["quality"] = quality["quality"] / quality["quality_max"]
        else:
            info["quality"] = quality["quality"]
        info["quality"] *= 100
        info["quality_bar"] = make_bar(info["quality"])
        info["quality"] = round(info["quality"])

        return info


class NetworkTraffic:
    """
    Retrieve network traffic information
    """

    pnic = None
    pnic_before = None

    def __init__(self, unknown_up, divisor, round_size):
        self.unknown_up = unknown_up
        self.divisor = divisor
        self.round_size = round_size

    def update_counters(self, interface):
        import psutil

        self.pnic_before = self.pnic
        counters = psutil.net_io_counters(pernic=True)
        self.pnic = counters[interface] if interface in counters else None

    def clear_counters(self):
        self.pnic_before = None
        self.pnic = None

    def get_bytes_sent(self):
        return (self.pnic.bytes_sent - self.pnic_before.bytes_sent) / self.divisor

    def get_bytes_received(self):
        return (self.pnic.bytes_recv - self.pnic_before.bytes_recv) / self.divisor

    def get_packets_sent(self):
        return self.pnic.packets_sent - self.pnic_before.packets_sent

    def get_packets_received(self):
        return self.pnic.packets_recv - self.pnic_before.packets_recv

    def get_rx_tot_Mbytes(self, interface):
        try:
            with open("/sys/class/net/{}/statistics/rx_bytes".format(interface)) as f:
                return int(f.readline().split('\n')[0]) / (1024 * 1024)
        except FileNotFoundError:
            return False

    def get_tx_tot_Mbytes(self, interface):
        try:
            with open("/sys/class/net/{}/statistics/tx_bytes".format(interface)) as f:
                return int(f.readline().split('\n')[0]) / (1024 * 1024)
        except FileNotFoundError:
            return False

    def get_usage(self, interface):
        self.update_counters(interface)
        usage = dict(bytes_sent=0, bytes_recv=0, packets_sent=0, packets_recv=0)

        if not sysfs_interface_up(interface, self.unknown_up) or not self.pnic_before:
            return usage
        else:
            usage["bytes_sent"] = self.get_bytes_sent()
            usage["bytes_recv"] = self.get_bytes_received()
            usage["packets_sent"] = self.get_packets_sent()
            usage["packets_recv"] = self.get_packets_received()
            usage["rx_tot_Mbytes"] = self.get_rx_tot_Mbytes(interface)
            usage["tx_tot_Mbytes"] = self.get_tx_tot_Mbytes(interface)
            round_dict(usage, self.round_size)
        return usage


class Network(IntervalModule, ColorRangeModule):
    """
    Displays network information for an interface.
    formatp support
    if u wanna display recv/send speed separate in dynamic color mode, please enable pango hint.

    Requires the PyPI packages `colour`, `netifaces`, `psutil` (optional, see below)
    and `basiciw` (optional, see below).

    .. rubric:: Available formatters

    Network Information Formatters:

    * `{interface}` — same as setting
    * `{v4}` — IPv4 address
    * `{v4mask}` — subnet mask
    * `{v4cidr}` — IPv4 address in cidr notation (i.e. 192.168.2.204/24)
    * `{v6}` — IPv6 address
    * `{v6mask}` — subnet mask
    * `{v6cidr}` — IPv6 address in cidr notation
    * `{mac}` — MAC of interface

    Wireless Information Formatters (requires PyPI package `basiciw`):

    * `{essid}` — ESSID of currently connected wifi
    * `{freq}` — Current frequency
    * `{quality}` — Link quality in percent
    * `{quality_bar}` —Bar graphically representing link quality

    Network Traffic Formatters (requires PyPI package `psutil`):

    * `{interface}` — the configured network interface
    * `{kbs}` – Float representing KiB\s corresponds to graph type
    * `{network_graph}` – Unicode graph representing network usage
    * `{bytes_sent}` — bytes sent per second (divided by divisor)
    * `{bytes_recv}` — bytes received per second (divided by divisor)
    * `{packets_sent}` — bytes sent per second (divided by divisor)
    * `{packets_recv}` — bytes received per second (divided by divisor)
    * `{rx_tot_Mbytes}` — total Mbytes received
    * `{tx_tot_Mbytes}` — total Mbytes sent
    """

    settings = (
        ("format_up", "format string"),
        ("format_down", "format string"),
        "color_up",
        "color_down",
        ("interface", "Interface to watch, eg 'eth0'"),
        ("dynamic_color", "Set color dynamically based on network traffic. Note: this overrides color_up"),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'"),
        ("graph_width", "Width of the network traffic graph"),
        ("graph_style", "Graph style ('blocks', 'braille-fill', 'braille-peak', or 'braille-snake')"),
        ("recv_limit", "Expected max KiB/s. This value controls the drawing color of receive speed"),
        ("sent_limit", "Expected max KiB/s. similar with receive_limit"),
        ("separate_color", "display recv/send color separate in dynamic color mode."
                           "Note: only network speed formatters will display with range color "),
        ("graph_type", "Whether to draw the network traffic graph for input or output. "
                       "Allowed values 'input' or 'output'"),
        ("divisor", "divide all byte values by this value"),
        ("ignore_interfaces", "Array of interfaces to ignore when cycling through "
                              "on click, eg, ['lo']"),
        ("round_size", "defines number of digits in round"),
        ("detached_down", "If the interface doesn't exist, display it as if it were down"),
        ("unknown_up", "If the interface is in unknown state, display it as if it were up"),
    )

    interval = 1
    interface = 'eth0'

    format_up = "{interface} {network_graph}{kbs}KB/s"
    format_down = "{interface}: DOWN"
    color_up = "#00FF00"
    color_down = "#FF0000"
    dynamic_color = True
    graph_type = 'input'
    graph_width = 15
    graph_style = 'blocks'
    recv_limit = 2048
    sent_limit = 1024
    separate_color = False

    # Network traffic settings
    divisor = 1024
    round_size = None

    # Network info settings
    detached_down = True
    unknown_up = False
    ignore_interfaces = ["lo"]

    on_leftclick = "nm-connection-editor"
    on_rightclick = "cycle_interface"
    on_upscroll = ['cycle_interface', 1]
    on_downscroll = ['cycle_interface', -1]

    def init(self):
        # Don't require importing basiciw unless using the functionality it offers.
        if any(s in self.format_down or s in self.format_up for s in
               ['essid', 'freq', 'quality', 'quality_bar']):
            get_wifi_info = True
        else:
            get_wifi_info = False

        self.network_info = NetworkInfo(self.interface, self.ignore_interfaces, self.detached_down, self.unknown_up,
                                        get_wifi_info)

        # Don't require importing psutil unless using the functionality it offers.
        if any(s in self.format_up or s in self.format_down for s in
               ['bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv', 'network_graph',
                'rx_tot_Mbytes', 'tx_tot_Mbytes', 'kbs']):
            self.network_traffic = NetworkTraffic(self.unknown_up, self.divisor, self.round_size)
        else:
            self.network_traffic = None

        if not self.dynamic_color:
            self.end_color = self.start_color = self.color_up
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, 100)
        self.kbs_arr = [0.0] * self.graph_width
        self.pango_enabled = self.hints.get("markup", False) and self.hints["markup"] == "pango"

    def cycle_interface(self, increment=1):
        """Cycle through available interfaces in `increment` steps. Sign indicates direction."""
        interfaces = [i for i in netifaces.interfaces() if i not in self.ignore_interfaces]
        if self.interface in interfaces:
            next_index = (interfaces.index(self.interface) + increment) % len(interfaces)
            self.interface = interfaces[next_index]
        elif len(interfaces) > 0:
            self.interface = interfaces[0]

        if self.network_traffic:
            self.network_traffic.clear_counters()
            self.kbs_arr = [0.0] * self.graph_width

    def get_network_graph(self, kbs, limit):
        # Cycle array by inserting at the start and chopping off the last element
        self.kbs_arr.insert(0, kbs)
        self.kbs_arr = self.kbs_arr[:self.graph_width]
        return make_graph(self.kbs_arr, 0.0, limit, self.graph_style)

    def run(self):
        format_values = dict(kbs="", network_graph="", bytes_sent="", bytes_recv="", packets_sent="", packets_recv="",
                             rx_tot_Mbytes="", tx_tot_Mbytes="",
                             interface="", v4="", v4mask="", v4cidr="", v6="", v6mask="", v6cidr="", mac="",
                             essid="", freq="", quality="", quality_bar="")
        if self.network_traffic:
            network_usage = self.network_traffic.get_usage(self.interface)
            format_values.update(network_usage)
            if self.graph_type == 'input':
                limit = self.recv_limit
                kbs = network_usage['bytes_recv'] * self.divisor / 1024
            elif self.graph_type == 'output':
                limit = self.sent_limit
                kbs = network_usage['bytes_sent'] * self.divisor / 1024
            else:
                raise Exception("graph_type must be either 'input' or 'output'!")

            format_values['network_graph'] = self.get_network_graph(kbs, limit)
            format_values['kbs'] = "{0:.1f}".format(round(kbs, 2))

            if self.separate_color and self.pango_enabled:
                color = self.color_up
                color_template = "<span color=\"{}\">{}</span>"
                per_recv = network_usage["bytes_recv"] * self.divisor / (self.recv_limit * 1024)
                per_sent = network_usage["bytes_sent"] * self.divisor / (self.sent_limit * 1024)
                c_recv = self.get_gradient(int(per_recv * 100), self.colors, 100)
                c_sent = self.get_gradient(int(per_sent * 100), self.colors, 100)
                format_values["bytes_recv"] = color_template.format(c_recv, network_usage["bytes_recv"])
                format_values["bytes_sent"] = color_template.format(c_sent, network_usage["bytes_sent"])
                if self.graph_type == 'output':
                    c_kbs = c_sent
                else:
                    c_kbs = c_recv
                format_values['network_graph'] = color_template.format(c_kbs, format_values["network_graph"])
                format_values['kbs'] = color_template.format(c_kbs, format_values["kbs"])
            else:
                percent = int(kbs * 100 / limit)
                color = self.get_gradient(percent, self.colors, 100)
        else:
            color = None

        if sysfs_interface_up(self.interface, self.unknown_up):
            if not color:
                color = self.color_up
            format_str = self.format_up
        else:
            color = self.color_down
            format_str = self.format_down

        network_info = self.network_info.get_info(self.interface)
        format_values.update(network_info)
        format_values['interface'] = self.interface

        self.data = format_values
        self.output = {
            "full_text": formatp(format_str, **format_values).strip(),
            'color': color,
        }
