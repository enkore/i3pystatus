import basiciw

from i3pystatus.network import Network


class Wireless(Network):
    """
    Display network information about a interface.

    Requires the PyPI packages `netifaces` and `basiciw`.

    This is based on the network module, so all options and formatters are
    the same, except for these additional formatters and that detached_down doesn't work.

    * `{essid}` — ESSID of currently connected wifi
    * `{freq}` — Current frequency
    * `{quality}` — Link quality in percent
    """

    interface = "wlan0"

    def collect(self):
        color, format, fdict, up = super().collect()

        if up:
            iwi = basiciw.iwinfo(self.interface)
            fdict["essid"] = iwi["essid"]
            fdict["freq"] = iwi["freq"]
            quality = iwi["quality"]
            if quality["quality_max"] > 0:
                fdict["quality"] = quality["quality"] / quality["quality_max"]
            else:
                fdict["quality"] = quality["quality"]
            fdict["quality"] *= 100
        else:
            fdict["essid"] = ""
            fdict["freq"] = fdict["quality"] = 0.0

        return color, format, fdict, up
