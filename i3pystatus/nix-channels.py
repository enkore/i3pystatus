# import os
import urllib.request
from i3pystatus.core.util import internet, require
from i3pystatus import IntervalModule, logger

class NixChannels(IntervalModule):

    """
    Gets update count for nix channels
    """
    settings = (
        ("color", "Text color when online"),
        ('color_offline', 'Text color when offline'),
        # ('format_online', 'Status text when online'),
        # ('format_offline', 'Status text when offline'),
        ("interval", "Update interval"),
    )

    color = '#ffffff'
    color_offline = '#ff0000'
    format_online = 'online'
    format_offline = 'offline'
    interval = 3600

    @require(internet)
    def run(self):
        url = "https://nixos.org/channels/nixos-unstable"
        conn = urllib.request.urlopen(url, timeout=30)
        last_modified = conn.headers['last-modified']

        # if internet():
        self.output = {
            "color": self.color,
            "full_text": "nixos-unstable: %s" % (last_modified)
        }
