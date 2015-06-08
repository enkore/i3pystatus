from i3pystatus import IntervalModule
import speedtest_cli
import requests
import time
import os
from urllib.parse import urlparse
import contextlib
import sys
from io import StringIO


class NetSpeed(IntervalModule):
    """
    Attempts to provide an estimation of internet speeds.
    Requires: speedtest_cli
    """

    settings = (
        ("url", "Target URL to download a file from. Uses speedtest_cli to "
            "find the 'best' server if none is supplied."),
        ("units", "Valid values are B, b, bytes, or bits"),
        "format"
    )
    color = "#FFFFFF"
    interval = 300
    url = None
    units = 'bits'
    format = "{speed} ({hosting_provider})"

    def run(self):

        # since speedtest_cli likes to print crap, we need to squelch it
        @contextlib.contextmanager
        def nostdout():
            save_stdout = sys.stdout
            sys.stdout = StringIO()
            yield
            sys.stdout = save_stdout

        if not self.url:
            with nostdout():
                try:
                    config = speedtest_cli.getConfig()
                    servers = speedtest_cli.closestServers(config['client'])
                    best = speedtest_cli.getBestServer(servers)
                    # 1500x1500 is about 4.3MB, which seems like a reasonable place to
                    # start, i guess...
                    url = '%s/random1500x1500.jpg' % os.path.dirname(best['url'])
                except KeyError:
                    url = None

        if not url:
            cdict = {
                "speed": 0,
                "hosting_provider": 'null',
            }
        else:
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

            if self.units == 'bits' or self.units == 'b':
                unit = 'bps'
                kilo = 1000
                mega = 1000000
                giga = 1000000000
                factor = 8
            elif self.units == 'bytes' or self.units == 'B':
                unit = 'Bps'
                kilo = 8000
                mega = 8000000
                giga = 8000000000
                factor = 1

            if total_length < kilo:
                bps = float(total_length / dl_time)

            if total_length >= kilo and total_length < mega:
                unit = "K" + unit
                bps = float((total_length / 1024.0) / dl_time)

            if total_length >= mega and total_length < giga:
                unit = "M" + unit
                bps = float((total_length / (1024.0 * 1024.0)) / dl_time)

            if total_length >= giga:
                unit = "G" + unit
                bps = float((total_length / (1024.0 * 1024.0 * 1024.0)) / dl_time)

            bps = "%.2f" % (bps * factor)
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
