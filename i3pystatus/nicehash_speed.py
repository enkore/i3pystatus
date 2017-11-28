import datetime
import requests
import re
import time
import json

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import internet, require, user_open

__author__ = "Fedor Marchenko"
__email__ = "mfs90@mail.ru"
__date__ = "Nov 09, 2017"


class NiceHashSpeed(IntervalModule):
    """Module for monitoring you miner statistic on nicehash.com
    Using public API <https://www.nicehash.com/doc-api>.

    .. rubric:: Available formatters

    * {addr}
    * {algo}
    * {status}
    * {speed}

    """

    settings = (
        ('addr', 'You BTC address'),
        ('algo', 'Algorithm number, for showing speed per one algorithm'),
        ('format', 'Format string used for output'),
        ('color', 'Standard color'),
        ('colorize', 'Enable color change on price increase/decrease'),
        ('color_up', 'Color for price increases'),
        ('color_down', 'Color for price decreases'),
        ('interval', 'Update interval.'),
        'status'
    )
    addr = '17a212wdrvEXWuipCV5gcfxdALfMdhMoqh'
    # Default: 20 = DaggerHashimoto
    algo = 20  # List of algorithm numbers may be looking on https://www.nicehash.com/doc-api.
    format = '{addr:.6}: {algo}[ {status}] {speed}'
    interval = 60
    color = '#FFFFFF'
    colorize = False
    color_up = '#00FF00'
    color_down = '#FF0000'
    status = {
        'speed_up': '▲',
        'speed_down': '▼',
    }

    _prev_speed = 0.0
    _prev_status = ''
    _prev_color = '#FFFFFF'

    _api_url = 'https://api.nicehash.com/api?method=stats.provider.ex&addr={addr}&from={from_unixtime}'
    _api_query_interval = 3

    def __init__(self, *args, **kwargs):
        super(NiceHashSpeed, self).__init__(*args, **kwargs)
        self.on_leftclick = [
            'open_something',
            'https://www.nicehash.com/miner/{}'.format(self.addr)
        ]

    def fetch_data(self):
        """Fetching statistic data from nicehash API for you BTC address

        :return: Return JSON data with statistic information about miners
        """
        with open('/tmp/nhapi.json', 'w+') as f:
            try:
                fetch_date_time = json.load(f).get('fetch_date_time')
                if (time.time() - fetch_date_time) < self._api_query_interval:
                    time.sleep(self._api_query_interval)
            except ValueError:
                json.dump({'fetch_date_time': time.time()}, f)
        return requests.get(self._api_url.format(addr=self.addr,
                                                 from_unixtime=(datetime.datetime.now() - datetime.timedelta(days=1))
                                                 .timestamp())).json()

    @require(internet)
    def run(self):
        try:
            data = self.fetch_data()
            error = data.get('result', {}).get('error')
            if error:
                if 'quota has been breached' in error:
                    m = re.search(r'in (\d+) sec', error)
                    time.sleep(int(m.groups()[0]))
                    return self.run()
                else:
                    self.output = {
                        'full_text': data.get('result', {})['error'],
                        'color': '#FF0000'
                    }
                    return
        except Exception as e:
            self.output = {
                'full_text': 'Failed fetching data from server: ' + str(e),
                'color': '#FF0000'
            }
            return

        algo = next(filter(lambda x: x.get('algo', None) == self.algo, data.get('result', {}).get('current', ({},))))
        speed = float(algo.get('data', ({},))[0].get('a', 0))

        fdict = {'addr': self.addr,
                 'algo': algo.get('name', ''),
                 'speed': '{:.2f}{}'.format(speed, algo.get('suffix', ''))}
        color = self.color

        if self._prev_speed and speed > self._prev_speed:
            color = self.color_up
            fdict['status'] = self.status['speed_up']
        elif self._prev_speed and speed < self._prev_speed:
            color = self.color_down
            fdict['status'] = self.status['speed_down']
        else:
            color = self._prev_color
            fdict['status'] = self._prev_status

        self._prev_speed = speed
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
