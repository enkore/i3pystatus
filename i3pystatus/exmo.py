# -*- coding: utf-8 -*-

import requests

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import internet, require, user_open


class Exmo(IntervalModule):
    """
    This module fetching and displays exchange rates with EXMO.
    Using API <https://exmo.me/en/api>.

    .. rubric:: Available formatters

    * {buy_price}
    * {status}
    * {pair}

    """

    settings = (
        ('format', 'Format string used for output'),
        ('pair', 'Currency pair for display on output'),
        ('color', 'Standard color'),
        ('colorize', 'Enable color change on price increase/decrease'),
        ('color_up', 'Color for price increases'),
        ('color_down', 'Color for price decreases'),
        ('interval', 'Update interval.'),
        'status'
    )
    format = '{buy_price}[ {status}] {pair}'
    pair = 'BTC_USD'
    color = '#FFFFFF'
    colorize = False
    color_up = '#00FF00'
    color_down = '#FF0000'
    interval = 60
    status = {
        'price_up': '▲',
        'price_down': '▼',
    }

    _prev_price = 0
    _prev_status = ''
    _prev_color = '#FFFFFF'

    def __init__(self, *args, **kwargs):
        super(Exmo, self).__init__(*args, **kwargs)
        self.on_leftclick = [
            'open_something',
            'https://exmo.me/ru/trade#?pair={}'.format(self.pair)
        ]

    def fetch_data(self):
        response = requests.get('https://api.exmo.com/v1/ticker/')
        return response.json()

    @require(internet)
    def run(self):
        price_data = self.fetch_data().get(self.pair)
        fdict = {
            'pair': self.pair.replace('_', '/'),
            'buy_price': price_data.get('buy_price', 0),
            'status': ''
        }
        color = self.color

        if self._prev_price and fdict['buy_price'] > self._prev_price:
            color = self.color_up
            fdict['status'] = self.status['price_up']
        elif self._prev_price and fdict['buy_price'] < self._prev_price:
            color = self.color_down
            fdict['status'] = self.status['price_down']
        else:
            color = self._prev_color
            fdict['status'] = self._prev_status

        self._prev_price = price_data.get('buy_price', 0)
        self._prev_status = fdict['status']
        self._prev_color = color

        if not self.colorize:
            color = self.color

        self.output = {
            'full_text': formatp(self.format, **fdict).strip(),
            'color': color
        }

    def open_something(self, url_or_command):
        """
        Wrapper function, to pass the arguments to user_open
        """
        user_open(url_or_command)
