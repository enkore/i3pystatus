import requests
import time

from i3pystatus import IntervalModule
from i3pystatus.core.util import bytes_info_dict


class Deluge(IntervalModule):
    """
    Deluge torrent module
    You will need to enable the web ui in deluge.
    Requires `requests`

    .. rubric:: Formatters:

    * `{num_torrents}`       - number of torrents in deluge
    * `{free_space_bytes}`   - bytes free in path
    * `{daemon_version}`     - current version of deluge running on the server
    * `{used_space_bytes}`   - bytes used in path
    * `{net_sent_sec_bytes}` - bytes sent per second
    * `{net_recv_sec_bytes}` - bytes received per second
    * `{net_sent_bytes}`     - bytes sent total
    * `{net_recv_bytes}`     - bytes received total

    .. rubric:: Unlisted Formatters:

    Deluge 2+ only:
    due to the sheer number of options in libtorrent, if you enable collection of
    libtorrent stats the keys are in the link below, just click 'session statistics'
    from the table of contents (for compatibility reasons, replace the fullstop in
    the name with an underscore, eg `net.recv_bytes` -> `net_recv_bytes`.
    https://www.libtorrent.org/manual-ref.html#session-statistics

    """
    # TODO: convert this module to run off a python library rather then requests
    #       i chose requests because at the time 2.0.0-b isnt supported by any
    #       libraries.

    settings = (
        ('format'),
        ('rounding', 'number of decimal places to round numbers too'),
        ('host', 'address of deluge server (default: 127.0.0.1)'),
        ('port', 'port of deluge server (default: 58846)'),
        ('password', 'password to authenticate to deluge (default: deluge)'),
        ('path', 'override "download path" server-side when checking space used/free'),
        ('libtorrent_stats', 'Deluge 2+ only. bool. set to True to pull all stats from libtorrent '
                             '(may cause high memory usage on older machines)(default: False)',
         )
    )

    host = '127.0.0.1'
    port = 8112
    password = 'deluge'
    path = None
    libtorrent_stats = False
    rounding = 2

    format = '⛆{num_torrents} ✇{free_space_bytes}'

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    id = int(time.time())  # something random

    def init(self):
        if any(s in self.format for s in ('net_sent_sec_bytes', 'net_recv_sec_bytes')):
            self.libtorrent_stats = True

        self.session = None
        self.last_tick = None
        self.last_session_statistics = None
        self.data = {}
        self.daemon_version = None

    def run(self):
        if not self.check_session():
            self.authenticate()

        if not self.daemon_version:
            self.daemon_version = self.detect_version()
            format_values = {'daemon_version': self.daemon_version}
        format_values = dict(num_torrents='', free_space='', daemon_version='', used_space='',
                             net_recv_sec_bytes='', net_sent_sec_bytes='')

        if self.libtorrent_stats:
            format_values.update(self.get_session_statistics())

            if self.daemon_version >= '2':
                def calculate_bytes_per_sec(key):
                    return (format_values[key] - self.last_session_statistics[key]) / (this_tick - self.last_tick)

                this_tick = time.time()
                if self.data is not None and self.last_session_statistics is not None:
                    format_values['net_sent_sec_bytes'] = calculate_bytes_per_sec('net_sent_bytes')
                    format_values['net_recv_sec_bytes'] = calculate_bytes_per_sec('net_recv_bytes')

                self.last_tick = float(this_tick)
                self.last_session_statistics = dict(format_values)

        torrents = self.get_torrents_status()
        if torrents:
            format_values['num_torrents'] = len(torrents)

        if 'free_space_bytes' in self.format:
            format_values['free_space_bytes'] = self.get_free_space(self.path)
        if 'used_space_bytes' in self.format:
            format_values['used_space_bytes'] = self.get_path_size(self.path)

        self.parse_values(format_values)

        self.data.update(format_values)
        self.output = {
            'full_text': self.format.format(**self.data)
        }

    def parse_values(self, values):
        for k, v in values.items():
            if v:
                if k.endswith('_bytes'):
                    values[k] = '{value:.{round}f}{unit}'.format(round=self.rounding, **bytes_info_dict(v))

    def authenticate(self):
        payload = self._gen_request('auth.login', [self.password])
        return self._send_request(payload)

    def check_session(self):
        payload = self._gen_request('auth.check_session')
        return self._send_request(payload)

    def get_path_size(self, path=None):
        """
        get used space of path in bytes (default: download location)
        """
        if path is None:
            path = []
        payload = self._gen_request('core.get_path_size', path)
        return self._send_request(payload)

    def get_free_space(self, path=None):
        """
        get free space of path in bytes (default: download location)
        """
        if path is None:
            path = []
        payload = self._gen_request('core.get_free_space', path)
        return self._send_request(payload)

    def get_torrents_status(self, torrent_id=None, keys=None):
        if torrent_id is None:
            torrent_id = []
        if keys is None:
            keys = []
        payload = self._gen_request('core.get_torrents_status', [torrent_id, keys])
        return self._send_request(payload)

    def detect_version(self):
        payload = self._gen_request('daemon.get_method_list')
        response = self._send_request(payload)
        if 'daemon.info' in response:
            ver_meth = 'daemon.info'
        else:
            ver_meth = 'daemon.get_version'

        payload = self._gen_request(ver_meth, [])
        daemon_version = self._send_request(payload)
        self.data['daemon_version'] = daemon_version
        return daemon_version

    def get_session_statistics(self):
        keys = []
        if self.data['daemon_version'] < '2':
            keys = [['upload_rate', 'download_rate', 'total_upload', 'total_download']]

        payload = self._gen_request('core.get_session_status', keys)
        response = self._send_request(payload)

        if self.data['daemon_version'] < '2':
            return {
                'net_sent_sec_bytes': response['upload_rate'],
                'net_recv_sec_bytes': response['download_rate'],
                'net_recv_bytes': response['total_download'],
                'net_sent_bytes': response['total_upload']
            }
        else:
            return {k.replace('.', '_'): v for k, v in response.items()}

    def _send_request(self, payload):
        if self.session is None:
            self.session = requests.Session()

        r = self.session.post('http://{}:{}/json'.format(self.host, self.port), headers=self.headers, json=payload)
        if r.ok:
            content = r.json()
            if not content['error']:
                return content['result']

    def _gen_request(self, method, args=None, kwargs=None):
        req = {"method": method, "id": self.id}
        if args is None:
            req['params'] = []
        else:
            req['params'] = args

        return req
