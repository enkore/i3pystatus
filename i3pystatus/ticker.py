from i3pystatus import IntervalModule
import yfinance as yf


class Ticker(IntervalModule):
    """
    Displays stock ticker information from yahoo finance
    Requires: yfinance
    """

    settings = (
        ("symbol", "Stock symbol to track"),
        ("interval", "Update interval (in seconds)"),
        ("good_color", "Color of text while 'regularMarketPrice' is above "
            "good_threshold"),
        ("bad_color", "Color of text while 'regularMarketPrice' is below "
            "bad_threshold"),
        ("caution_color", "Color of text while 'regularMarketPrice' is between good "
            "and bad thresholds"),
        ("good_threshold", "The target value for consindering the stock a good value"),
        ("bad_threshold", "The target value for consindering the stock a poor value"),
        "format"
    )
    required = ("symbol",)
    good_color = "#00FF00"     # green
    caution_color = "#FFFF00"  # yellow
    bad_color = "#FF0000"      # red
    good_threshold = 100
    bad_threshold = 50
    interval = 300
    format = "{symbol}: {regularMarketPrice} ({regularMarketDayHigh}/{regularMarketDayLow})"

    def run(self):

        stock = yf.Ticker(self.symbol)
        tick = stock.info

        if tick['regularMarketPrice'] >= float(self.good_threshold):
            color = self.good_color
        elif tick['regularMarketPrice'] <= float(self.bad_threshold):
            color = self.bad_color
        else:
            color = self.caution_color

        self.output = {
            "full_text": self.format.format(**tick),
            "color": color
        }
