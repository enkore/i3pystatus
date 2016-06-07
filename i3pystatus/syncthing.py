import json
import os.path
import requests
from subprocess import call
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from i3pystatus import IntervalModule
from i3pystatus.core.util import user_open


class Syncthing(IntervalModule):
    """
    Check Syncthing's online status and start/stop Syncthing via
    click events.

    Requires `requests`.
    """

    format_up = 'ST up'
    color_up = '#00ff00'
    format_down = 'ST down'
    color_down = '#ff0000'
    configfile = '~/.config/syncthing/config.xml'
    url = 'auto'
    apikey = 'auto'
    verify_ssl = True
    interval = 10
    on_leftclick = 'st_open'
    on_rightclick = 'st_toggle_systemd'

    settings = (
        ('format_up', 'Text to show when Syncthing is running'),
        ('format_down', 'Text to show when Syncthing is not running'),
        ('color_up', 'Color when Syncthing is running'),
        ('color_down', 'Color when Syncthing is not running'),
        ('configfile', 'Path to Syncthing config'),
        ('url', 'Syncthing GUI URL; "auto" reads from local config'),
        ('apikey', 'Syncthing APIKEY; "auto" reads from local config'),
        ('verify_ssl', 'Verify SSL certificate'),
    )

    def st_get(self, endpoint):
        # TODO: Maybe we can share a session across multiple GETs.
        with requests.Session() as s:
            r = s.get(self.url)
            csrf_name, csfr_value = r.headers['Set-Cookie'].split('=')
            s.headers.update({'X-' + csrf_name: csfr_value})
            r = s.get(
                urljoin(self.url, endpoint),
                verify=self.verify_ssl,
            )
        return json.loads(r.text)

    def st_post(self, endpoint, data=None):
        headers = {'X-API-KEY': self.apikey}
        requests.post(
            urljoin(self.url, endpoint),
            data=data,
            headers=headers,
        )

    def read_config(self):
        self.configfile = os.path.expanduser(self.configfile)
        # Parse config only once!
        if self.url == 'auto' or self.apikey == 'auto':
            tree = ET.parse(self.configfile)
            root = tree.getroot()
            if self.url == 'auto':
                tls = root.find('./gui').attrib['tls']
                address = root.find('./gui/address').text
                if tls == 'true':
                    self.url = 'https://' + address
                else:
                    self.url = 'http://' + address
            if self.apikey == 'auto':
                self.apikey = root.find('./gui/apikey').text

    def ping(self):
        try:
            ping_data = self.st_get('/rest/system/ping')
            if ping_data['ping'] == 'pong':
                return True
            else:
                return False
        except requests.exceptions.ConnectionError:
            return False

    def run(self):
        self.read_config()
        self.online = True if self.ping() else False

        if self.online:
            self.output = {
                'full_text': self.format_up,
                'color': self.color_up
            }
        else:
            self.output = {
                'full_text': self.format_down,
                'color': self.color_down
            }

    # Callbacks
    def st_open(self):
        """Callback: Open Syncthing web UI"""
        user_open(self.url)

    def st_restart(self):
        """Callback: Restart Syncthing"""
        self.st_post('/rest/system/restart')

    def st_stop(self):
        """Callback: Stop Syncthing"""
        self.st_post('/rest/system/shutdown')

    def st_start_systemd(self):
        """Callback: systemctl --user start syncthing.service"""
        call(['systemctl', '--user', 'start', 'syncthing.service'])

    def st_restart_systemd(self):
        """Callback: systemctl --user restart syncthing.service"""
        call(['systemctl', '--user', 'restart', 'syncthing.service'])

    def st_stop_systemd(self):
        """Callback: systemctl --user stop syncthing.service"""
        call(['systemctl', '--user', 'stop', 'syncthing.service'])

    def st_toggle_systemd(self):
        """Callback: start Syncthing service if offline, or stop it when online"""
        if self.online:
            self.st_stop_systemd()
        else:
            self.st_start_systemd()
