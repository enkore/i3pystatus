from i3pystatus import IntervalModule
import speedtest_cli
import requests
import time
import os
from urllib.parse import urlparse


class NetSpeed(IntervalModule):
    """
    Attempts to provide an estimation of internet speeds.
    Requires: speedtest_cli
    """

    settings = (
        ("url", "Target URL to download a file from. Uses speedtest_cli to "
            "find the 'best' server if none is supplied."),
        "format"
    )
    color = "#FFFFFF"
    interval = 300
    url = None
    format = "{speed} ({hosting_provider})"

    def run(self):
        if not self.url:
            config = speedtest_cli.getConfig()
            servers = speedtest_cli.closestServers(config['client'])
            best = speedtest_cli.getBestServer(servers)
            # 1500x1500 is about 4.3MB, which seems like a reasonable place to
            # start, i guess...
            url = '%s/random1500x1500.jpg' % os.path.dirname(best['url'])

        with open('/dev/null', 'wb') as devnull:
            start = time.time()
            req = requests.get(url, stream=True)
            devnull.write(req.content)
            end = time.time()
            total_length = int(req.headers.get('content-length'))
        devnull.close()

        # chop off the float after the 4th decimal point
        # note: not rounding, simply cutting
        # note: dl_time is in seconds
        dl_time = float(end - start)

        if total_length < 999:
            unit = "Bps"
            bps = total_length / dl_time

        if total_length >= 1000 < 999999:
            unit = "KBps"
            bps = (total_length / 1024.0) / dl_time

        if total_length >= 1000000 < 999999999:
            unit = "MBps"
            bps = (total_length / (1024.0 * 1024.0)) / dl_time

        if total_length >= 10000000:
            unit = "GBps"
            bps = (total_length / (1024.0 * 1024.0 * 1024.0)) / dl_time

        bps = "%.2f" % bps
        speed = "%s %s" % (bps, unit)
        hosting_provider = '.'.join(urlparse(url).hostname.split('.')[-2:])

        cdict = {
            "speed": speed,
            "hosting_provider": hosting_provider,
        }

        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.color
        }
