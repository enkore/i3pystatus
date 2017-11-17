import requests
import json
from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require

class Coin(IntervalModule):
    """
    Fetches live data of various cryptocurrencies from https://coinmarketcap.com/
    coin setting should be equal to the 'id' field of your coin in https://api.coinmarketcap.com/v1/ticker/
    example coin settings: bitcoin, bitcoin-cash, ethereum, litecoin, dash, lisk
    example currency settings: usd, eur, huf

    .. rubric:: Available formatters
    * {symbol}
    * {price}
    * {rank}
    * {24h_volume}
    * {market_cap}
    * {available_supply}
    * {total_supply}
    * {max_supply}
    * {percent_change_1h}
    * {percent_change_24h}
    * {percent_change_7d}
    * {last_updated}         //on website
    * {status}
    """

    settings = (
        ("format",          "format string used for output."),
        ("coin",            "cryptocurrency to fetch"),
        ("currency",        "fiat currency to show fiscal data"),
        ("symbol",          "coin symbol"),
        ("interval",        "update interval in seconds"),
        ("status_interval", "percent change status in the last: '1h' / '24h' / '7d'")
    )

    symbol = "¤"
    format = "{symbol} {price}{status}"
    coin = "ethereum"
    currency = "USD"
    interval = 600
    status_interval = "24h"

    def fetch_data(self):
        response = requests.get("https://api.coinmarketcap.com/v1/ticker/{}/?convert={}".format(self.coin, self.currency))
        coin_data = response.json()[0]
        coin_data["price"] = coin_data.pop("price_{}".format(self.currency.lower()))
        coin_data["24h_volume"] = coin_data.pop("24h_volume_{}".format(self.currency.lower()))
        coin_data["market_cap"] = coin_data.pop("market_cap_{}".format(self.currency.lower()))
        coin_data["symbol"] = self.symbol
        return coin_data

    def set_status(self, change):
        if change > 10:
            return '⮅'
        elif change > 0:
            return '⭡'
        elif change < -10:
            return '⮇'
        elif change < 0:
            return '⭣'
        else:
            return ''

    @require(internet)
    def run(self):
        fdict = self.fetch_data()

        symbols = dict(bitcoin='฿', ethereum='Ξ', litecoin='Ł', dash='Đ')
        if self.coin in symbols:
            fdict["symbol"] = symbols[self.coin]
        fdict["status"] = self.set_status(float(fdict["percent_change_{}".format(self.status_interval)]))

        self.data = fdict
        self.output = {"full_text": self.format.format(**fdict)}
