import basiciw

from i3pystatus.network import Network

class Wireless(Network):
    """
    Display network information about a interface.

    Requires the PyPI packages `netifaces-py3` and `basiciw`.

    This is based on the network module, so all options and formatters are
    the same, except for these additional formatters:
    * {essid} ESSID of currently connected wifi
    * {freq} Current frequency
    * {quality} Link quality in percent
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
                fdict["quality"] = round(quality["quality"] / quality["quality_max"],3)
            else:
                fdict["quality"] = round(quality["quality"],3)
            fdict["quality"] *= 100
        else:
            fdict["essid"] = ""
            fdict["freq"] = fdict["quality"] = 0.0

        return (color, format, fdict, up)
