import urllib.request
import json
from datetime import datetime

from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require, user_open

import locale
import threading
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()


@contextmanager
def setlocale(name):
    # To deal with locales only in this module and keep it thread save
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


class Bitcoin(IntervalModule):

    """
    This module fetches and displays current Bitcoin market prices and
    optionally monitors transactions to and from a list of user-specified
    wallet addresses. Market data is pulled from the Bitaps Market
    API <https://bitaps.com> and it is possible to specify
    the exchange to be monitored.
    Transaction data is pulled from blockchain.info
    <https://blockchain.info/api/blockchain_api>.

    .. rubric:: Available formatters

    * {last_price}
    * {status}
    * {symbol}

    """

    settings = (
        ("format", "Format string used for output."),
        ("currency", "Base fiat currency used for pricing."),
        # ("wallet_addresses", "List of wallet address(es) to monitor."),
        ("color", "Standard color"),
        # ("exchange", "Get ticker from a custom exchange instead"),
        ("colorize", "Enable color change on price increase/decrease"),
        ("color_up", "Color for price increases"),
        ("color_down", "Color for price decreases"),
        ("interval", "Update interval."),
        ("symbol", "Symbol for bitcoin sign"),
        "status"
    )
    format = "{symbol} {status}{last_price}"
    currency = "USD"
    exchange = "blockchain.info"
    symbol = "\uF15A"
    wallet_addresses = ""
    color = "#FFFFFF"
    colorize = False
    color_up = "#00FF00"
    color_down = "#FF0000"
    interval = 600
    status = {
        "price_up": "▲",
        "price_down": "▼",
    }

    on_leftclick = "electrum"
    on_rightclick = ["open_something", "https://bitaps.com/"]

    _price_prev = 0

    def _get_age(self, bitcoinaverage_timestamp):
        with setlocale('C'):  # Deal with locales (months name differ)
            # Assume format is always utc, to avoid import pytz
            diff = datetime.utcnow() - \
                datetime.fromtimestamp(bitcoinaverage_timestamp)
        return int(diff.total_seconds())

    def _query_api(self, api_url):
        url = "{}".format(api_url)
        response = urllib.request.urlopen(url).read().decode("utf-8")
        return json.loads(response)

    def _fetch_price_data(self):
        api_url = "https://blockchain.info/ticker"
        ret = self._query_api(api_url)
        return ret[self.currency.upper()]

    def _fetch_blockchain_data(self):
        api = "https://blockchain.info/multiaddr?active="
        addresses = "|".join(self.wallet_addresses)
        url = "{}{}".format(api, addresses)
        return json.loads(urllib.request.urlopen(url).read().decode("utf-8"))

    @require(internet)
    def run(self):
        price_data = self._fetch_price_data()

        fdict = {
            "symbol": self.symbol,
            "last_price": float(price_data["last"]),
        }

        if self._price_prev and fdict["last_price"] > self._price_prev:
            color = self.color_up
            fdict["status"] = self.status["price_up"]
        elif self._price_prev and fdict["last_price"] < self._price_prev:
            color = self.color_down
            fdict["status"] = self.status["price_down"]
        else:
            color = self.color
            fdict["status"] = ""
        self._price_prev = fdict["last_price"]

        if not self.colorize:
            color = self.color

        self.data = fdict
        self.output = {
            "full_text": self.format.format(**fdict),
            "color": color,
        }

    def open_something(self, url_or_command):
        """
        Wrapper function, to pass the arguments to user_open
        """
        user_open(url_or_command)
