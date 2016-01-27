from i3pystatus import IntervalModule
import requests
import json
from i3pystatus.core import ConfigError
from i3pystatus.core.util import user_open, internet, require


class Github(IntervalModule):
    """
    Check Github for pending notifications.
    Requires `requests`

    Formatters:

    * `{unread}`        — contains the value of unread_marker when there are pending notifications
    * `{unread_count}`  — number of unread notifications, empty if 0
    """

    max_error_len = 50
    unread_marker = "●"
    unread = ''
    color = '#78EAF2'
    username = ''
    password = ''
    format = '{unread}'
    interval = 600
    keyring_backend = None

    on_leftclick = 'open_github'

    settings = (
        ('format', 'format string'),
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
        ('unread_marker', 'sets the string that the "unread" formatter shows when there are pending notifications'),
        ("username", ""),
        ("password", ""),
        ("color", "")
    )

    def open_github(self):
        user_open('https://github.com/' + self.username)

    @require(internet)
    def run(self):
        format_values = dict(unread_count='', unread='')

        response = requests.get('https://api.github.com/notifications', auth=(self.username, self.password))
        data = json.loads(response.text)

        # Bad credentials
        if isinstance(data, dict):
            err_msg = data['message']
            raise ConfigError(err_msg)

        unread = len(data)
        if unread > 0:
            format_values['unread_count'] = unread
            format_values['unread'] = self.unread_marker

        self.data = format_values
        self.output = {
            'full_text': self.format.format(**format_values),
            'color': self.color
        }
