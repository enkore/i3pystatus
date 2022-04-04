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
    # https://channels.nix.gsc.io/ is a non official service and requests to not be polled
    # more frequently than every 15 mn
    interval = 3600

    @require(internet)
    def run(self):
        url = f"https://channels.nix.gsc.io/{self.channel}/latest-url"
        conn = urllib.request.urlopen(url, timeout=30)
        advancement_timestamp = conn.read().decode().split()[-1]
        # print()
        # last_modified = conn.headers['last-modified']
        last_modified = datetime.datetime.fromtimestamp(int(advancement_timestamp))
        # outstr = today.strftime(self.prefixformat) + " "
        span = datetime.datetime.now() - last_modified

        # if internet():
        self.output = {
            "color": self.color,
            "full_text": "%s" % (span)
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
