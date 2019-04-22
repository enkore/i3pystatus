import time

from deluge_client import DelugeRPCClient, FailedToReconnectException

from i3pystatus import IntervalModule, logger
from i3pystatus.core.util import bytes_info_dict


class Deluge(IntervalModule):
    """
    Deluge torrent module
    Requires `deluge-client`

    .. rubric:: Formatters:

    * `{num_torrents}`       - number of torrents in deluge
    * `{free_space_bytes}`   - bytes free in path
    * `{used_space_bytes}`   - bytes used in path
    * `{upload_rate}` - bytes sent per second
    * `{download_rate}` - bytes received per second
    * `{total_uploaded}`     - bytes sent total
    * `{total_downloaded}`     - bytes received total

    """

    settings = (
        'format',
        'color',
        ('rounding', 'number of decimal places to round numbers too'),
        ('host', 'address of deluge server (default: 127.0.0.1)'),
        ('port', 'port of deluge server (default: 58846)'),
        ('username', 'username to authenticate with deluge'),
        ('password', 'password to authenticate to deluge'),
        ('path', 'override "download path" server-side when checking space used/free'),
        ('offline_string', 'string to output while unable to connect to deluge daemon')
    )
    required = ('username', 'password')

    host = '127.0.0.1'
    port = 58846
    path = None
    color = None
    libtorrent_stats = False
    rounding = 2
    offline_string = 'offline'

    format = '⛆{num_torrents} ✇{free_space_bytes}'

    id = int(time.time())  # something random

    def init(self):
        self.client = DelugeRPCClient(self.host, self.port, self.username, self.password)
        self.data = {}

    def run(self):
        if not self.client.connected:
            try:
                self.client.connect()
            except OSError:
                self.output = {
                    'full_text': self.offline_string
                }
                return

        try:
            self.data = self.get_session_statistics()

            torrents = self.get_torrents_status()
            if torrents:
                self.data['num_torrents'] = len(torrents)

            if 'free_space_bytes' in self.format:
                self.data['free_space_bytes'] = self.get_free_space(self.path)
            if 'used_space_bytes' in self.format:
                self.data['used_space_bytes'] = self.get_path_size(self.path)
        except FailedToReconnectException:
            return

        self.parse_values(self.data)

        self.output = {
            'full_text': self.format.format(**self.data)
        }
        if self.color:
            self.output['color'] = self.color

    def parse_values(self, values):
        for k, v in values.items():
            if v:
                if k in ['total_upload', 'total_download', 'download_rate', 'upload_rate'] or k.endswith('_bytes'):
                    values[k] = '{value:.{round}f}{unit}'.format(round=self.rounding, **bytes_info_dict(v))

    def get_path_size(self, path=None):
        """
        get used space of path in bytes (default: download location)
        """
        if path is None:
            path = []
        return self.client.call('core.get_path_size', path)

    def get_free_space(self, path=None):
        """
        get free space of path in bytes (default: download location)
        """
        if path is None:
            path = []
        return self.client.call('core.get_free_space', path)

    def get_torrents_status(self, torrent_id=None, keys=None):
        if torrent_id is None:
            torrent_id = []
        if keys is None:
            keys = []
        return self.client.call('core.get_torrents_status', torrent_id, keys)

    def get_session_statistics(self):
        keys = ['upload_rate', 'download_rate', 'total_upload', 'total_download']

        out = {}  # some of the values from deluge-client are bytes, the others are ints - we need to decode them
        for k, v in self.client.call('core.get_session_status', keys).items():
            k = k.decode('utf-8')  # keys aswell
            if type(v) == bytes:
                out[k] = v.decode('utf-8')
            else:
                out[k] = v

        return out
