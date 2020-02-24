# import os
import urllib.request
from i3pystatus.core.util import internet, require
from i3pystatus import IntervalModule, logger
import datetime

class NixChannels(IntervalModule):

    """
    Gets update count for nix channels
    """
    settings = (
        ("color", "Text color when online"),
        ('color_offline', 'Text color when offline'),
        ('channel', 'Name of the channel'),
        ('format_online', 'Status text when online'),
        # ('format_offline', 'Status text when offline'),
        ("interval", "Update interval"),
    )

    color = '#ffffff'
    channel = 'nixos-unstable'
    color_offline = '#ff0000'
    format_online = 'online'
    format_offline = 'offline'
    interval = 3600

    @require(internet)
    def run(self):
        url = "https://nixos.org/channels/%s" % self.channel
        conn = urllib.request.urlopen(url, timeout=30)
        last_modified = conn.headers['last-modified']

        # outstr = today.strftime(self.prefixformat) + " "
        span = last_update - datetime.now()

        # if internet():
        self.output = {
            "color": self.color,
            "full_text": "nixos-unstable: %s" % (span)
        }


    # upon update trigger notification ?
    # def report(self):
    #     DesktopNotification(
    #         title=formatp(self.format_summary, **self.data).strip(),
    #         body="\n".join(self.notif_body.values()),
    #         icon=self.notification_icon,
    #         urgency=1,
    #         timeout=0,
    #     ).display()
