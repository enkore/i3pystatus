from i3pystatus import IntervalModule, formatp

import GeoIP
import urllib.request


class ExternalIP(IntervalModule):
    """
    Shows the external IP with the country code/name.

    Requires the PyPI package `GeoIP`.

    .. rubric:: Available formatters

    * {country_name} the full name of the country from the IP (eg. 'United States')
    * {country_code} the country code of the country from the IP (eg. 'US')
    * {ip} the ip
    """

    settings = (
        "format",
        "color",
        ("color_down", "color when the http request failed"),
        ("color_hide", "color when the user has decide to switch to the hide format"),
        ("format_down", "format when the http request failed"),
        ("format_hide", "format when the user has decide to switch to the hide format"),
        ("ip_website", "http website where the IP is directly available as raw"),
        ("timeout", "timeout in seconds when the http request is taking too much time"),
    )

    interval = 15
    format = "{country_name} {country_code} {ip}"
    format_hide = "{country_code}"
    format_down = "Timeout"

    ip_website = "https://api.ipify.org"
    timeout = 5
    color = "#FFFFFF"
    color_hide = "#FFFF00"
    color_down = "#FF0000"

    on_leftclick = "switch_hide"
    on_rightclick = "run"

    def run(self):
        try:
            request = urllib.request.urlopen(self.ip_website,
                                             timeout=self.timeout)
            ip = request.read().decode().strip()
        except Exception:
            return self.disable()

        gi = GeoIP.GeoIP(GeoIP.GEOIP_STANDARD)
        country_code = gi.country_code_by_addr(ip)
        country_name = gi.country_name_by_addr(ip)

        if not ip or not country_code:
            return self.disable()  # fail here in the case of a bad IP

        fdict = {
            "country_name": country_name,
            "country_code": country_code,
            "ip": ip
        }

        self.output = {
            "full_text": formatp(self.format, **fdict).strip(),
            "color": self.color
        }

    def disable(self):
        self.output = {
            "full_text": self.format_down,
            "color": self.color_down
        }

    def switch_hide(self):
        self.format, self.format_hide = self.format_hide, self.format
        self.color, self.color_hide = self.color_hide, self.color
        self.run()
