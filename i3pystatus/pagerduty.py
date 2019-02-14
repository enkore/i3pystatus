from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require, formatp

import pypd

__author__ = 'chestm007'


class PagerDuty(IntervalModule):
    """
    Module to get the current incidents in PD
    Requires `pypd`

    Formatters:

    * `{num_incidents}` - current number of incidents unresolved
    * `{num_acknowledged_incidents}` - as it sounds
    * `{num_triggered_incidents}` - number of unacknowledged incidents

    Example

    .. code-block:: python

        status.register(
            'pagerduty',
            api_key=mah_api_key,
            user_id=LKJ19QW
        )

    """
    settings = (
        'format',
        'api_key',
        'color',
        'interval',
        ('user_id', 'your pagerduty user id, shows up in the url when viewing your profile '
                    '`https://subdomain.pagerduty.com/users/<user_id>')
    )

    required = ('api_key', )

    format = '{num_triggered_incidents} triggered  {num_acknowledged_incidents} acknowledged'
    api_key = None
    color = '#AA0000'
    interval = 60
    user_id = None
    api_search_dict = dict(statuses=['triggered', 'acknowledged'])

    num_acknowledged_incidents = None
    num_triggered_incidents = None
    num_incidents = None

    def init(self):
        pypd.api_key = self.api_key
        if self.user_id:
            self.api_search_dict['user_ids'] = [self.user_id]

    @require(internet)
    def run(self):
        pd_incidents = pypd.Incident.find(**self.api_search_dict)

        incidents = {
            'acknowledged': [],
            'triggered': [],
            'all': []
        }
        for incident in pd_incidents:
            incidents['all'].append(incident)
            status = incident.get('status')
            if status == 'acknowledged':
                incidents['acknowledged'].append(incident)
            elif status == 'triggered':
                incidents['triggered'].append(incident)
        self.num_acknowledged_incidents = len(incidents.get('acknowledged'))
        self.num_triggered_incidents = len(incidents.get('triggered'))
        self.num_incidents = len(incidents.get('all'))

        self.output = dict(
            full_text=formatp(self.format, **vars(self)),
            color=self.color
        )
