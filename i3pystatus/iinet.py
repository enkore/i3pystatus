import requests

from i3pystatus import IntervalModule
from i3pystatus.core.color import ColorRangeModule

__author__ = 'facetoe'


class IINet(IntervalModule, ColorRangeModule):
    """
    Check IINet Internet usage.
    Requires `requests` and `colour`

    Formatters:

    * `{percentage_used}`        — percentage of your quota that is used
    * `{percentage_available}`   — percentage of your quota that is available
    """

    settings = (
        "format",
        ("username", "Username for IINet"),
        ("password", "Password for IINet"),
        ("start_color", "Beginning color for color range"),
        ("end_color", "End color for color range")
    )

    format = '{percent_used}'
    start_color = "#00FF00"
    end_color = "#FF0000"

    username = None
    password = None

    keyring_backend = None

    def init(self):
        self.token = None
        self.service_token = None
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, 100)

    def set_tokens(self):
        if not self.token or not self.service_token:
            response = requests.get('https://toolbox.iinet.net.au/cgi-bin/api.cgi?'
                                    '_USERNAME=%(username)s&'
                                    '_PASSWORD=%(password)s'
                                    % self.__dict__).json()

            if self.valid_response(response):
                self.token = response['token']
                self.service_token = self.get_service_token(response['response']['service_list'])

            else:
                raise Exception("Failed to retrieve token for user: %s" % self.username)

    def get_service_token(self, service_list):
        for service in service_list:
            if service['pk_v'] == self.username:
                return service['s_token']
        raise Exception("Failed to retrieve service token for user: %s" % self.username)

    def valid_response(self, response):
        return "success" in response and response['success'] == 1

    def run(self):
        self.set_tokens()

        usage = self.get_usage()
        allocation = usage['allocation']
        used = usage['used']

        percent_used = self.percentage(used, allocation)
        percent_avaliable = self.percentage(allocation - used, allocation)
        color = self.get_gradient(percent_used, self.colors)

        usage['percent_used'] = '{0:.2f}%'.format(percent_used)
        usage['percent_available'] = '{0:.2f}%'.format(percent_avaliable)

        self.data = usage
        self.output = {
            "full_text": self.format.format(**usage),
            "color": color
        }

    def get_usage(self):
        response = requests.get('https://toolbox.iinet.net.au/cgi-bin/api.cgi?Usage&'
                                '_TOKEN=%(token)s&'
                                '_SERVICE=%(service_token)s' % self.__dict__).json()
        if self.valid_response(response):
            for traffic_type in response['response']['usage']['traffic_types']:
                if traffic_type['name'] == 'anytime':
                    return traffic_type
        else:
            raise Exception("Failed to retrieve usage information for: %s" % self.username)
