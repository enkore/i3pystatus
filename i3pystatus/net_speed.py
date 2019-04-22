from i3pystatus import IntervalModule
import speedtest
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
    Requires: speedtest-cli/modularize-2
    speedtest-cli/modularize-2 can be installed using pip:
    `pip install git+https://github.com/sivel/speedtest-cli.git@modularize-2`
    """

    settings = (
        ("units", "Valid values are B, b, bytes, or bits"),
        "format",
        'color'
    )
    color = "#FFFFFF"
    interval = 300
    units = 'bits'
    format = "↓{speed_down:.1f}{down_units} ↑{speed_up:.1f}{up_units} ({hosting_provider})"

    def form_b(self, n: float)->tuple:
        """
        formats a bps as bps/kbps/mbps/gbps etc
        handles whether its meant to be in bytes
        :param n: input float
        :rtype tuple:
        :return: tuple of float-number of mbps etc, str-units
        """
        unit = 'bps'
        kilo = 1000
        mega = 1000000
        giga = 1000000000
        bps = 0

        if self.units == 'bytes' or self.units == 'B':
            unit = 'Bps'
            kilo = 8000
            mega = 8000000
            giga = 8000000000

        if n < kilo:
            bps = float(n)

        if n >= kilo and n < mega:
            unit = "K" + unit
            bps = float(n / 1024.0)

        if n >= mega and n < giga:
            unit = "M" + unit
            bps = float(n / (1024.0 * 1024.0))

        if n >= giga:
            unit = "G" + unit
            bps = float(n / (1024.0 * 1024.0 * 1024.0))

        return bps, unit

    def run(self):
        # since speedtest_cli likes to print crap, we need to squelch it
        @contextlib.contextmanager
        def nostdout():
            save_stdout = sys.stdout
            sys.stdout = StringIO()
            yield
            sys.stdout = save_stdout

        cdict = {
            "speed_up": 0.0,
            "speed_down": 0.0,
            "down_units": "",
            "up_units": "",
            "hosting_provider": 'null'
        }
        st = None
        with nostdout():
            try:
                # this is now the canonical way to use speedtest_cli as a module.
                st = speedtest.Speedtest()
            except speedtest.ConfigRetrievalError:
                # log('Cannot retrieve speedtest configuration')
                self.output = {}
            if st:
                try:
                    # get the servers
                    st.get_servers()
                    st.get_best_server()

                except speedtest.ServersRetrievalError:
                    # log this somehow
                    # log('Cannot retrieve speedtest server list')
                    pass
                results = st.results

                down, up = st.download(), st.upload()
                speed_down, down_units = self.form_b(down)
                speed_up, up_units = self.form_b(up)

                cdict = {
                    "speed_down": speed_down,
                    "speed_up": speed_up,
                    "up_units": up_units,
                    "down_units": down_units,
                    "hosting_provider": results.server.get("sponsor", "Unknown Provider")
                }

        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.color
        }
