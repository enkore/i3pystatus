import os

import dateutil.parser

from travispy import TravisPy

from i3pystatus import IntervalModule
from i3pystatus.core.util import TimeWrapper, formatp, internet, require

__author__ = 'chestm007'


class TravisCI(IntervalModule):
    """
    Get current status of travis builds
    Requires `travispy` `dateutil.parser`

    Formatters:

    * `{repo_slug}`  - repository owner/repository name
    * `{repo_status}` - repository status
    * `{repo_name}` - repository name
    * `{repo_owner}` - repository owner
    * `{last_build_finished}` - date of the last finished build
    * `{last_build_duration}` - duration of the last build


    Examples

    .. code-block:: python

        status_color_map = {
            'passed': '#00FF00',
            'failed': '#FF0000',
            'errored': '#FFAA00',
            'cancelled': '#EEEEEE',
            'started': '#0000AA',

        }

    .. code-block:: python

        repo_status_map={
            'passed': '<span color="#00af00">passed</span>',
            'started': '<span color="#0000af">started</span>',
            'failed': '<span color="#af0000">failed</span>',
        }

    """

    settings = (
        'format',
        ('github_token', 'github personal access token'),
        ('repo_slug', 'repository identifier eg. "enkore/i3pystatus"'),
        ('time_format', 'passed directly to .strftime() for `last_build_finished`'),
        ('repo_status_map', 'map representing how to display status'),
        ('duration_format', '`last_build_duration` format string'),
        ('status_color_map', 'color for all text based on status'),
        ('color', 'color for all text not otherwise colored'))

    required = ('github_token', 'repo_slug')

    format = '{repo_owner}/{repo_name}-{repo_status} [({last_build_finished}({last_build_duration}))]'
    short_format = '{repo_name}-{repo_status}'
    time_format = '%m/%d'
    duration_format = '%m:%S'
    status_color_map = None
    repo_status_map = None
    color = '#DDDDDD'
    travis = None

    on_leftclick = 'open_build_webpage'

    def init(self):
        self.repo_status = None
        self.last_build_duration = None
        self.last_build_finished = None
        self.repo_owner, self.repo_name = self.repo_slug.split('/')

    def _format_time(self, time):
        _datetime = dateutil.parser.parse(time)
        return _datetime.strftime(self.time_format)

    @require(internet)
    def run(self):
        if self.travis is None:
            self.travis = TravisPy.github_auth(self.github_token)
        repo = self.travis.repo(self.repo_slug)

        self.repo_status = self.repo_status_map.get(repo.last_build_state, repo.last_build_state)

        self.last_build_id = repo.last_build_id

        if repo.last_build_state == 'started':
            self.last_build_finished = None
            self.last_build_duration = None

        elif repo.last_build_state in ('failed', 'errored', 'cancelled', 'passed'):
            self.last_build_finished = self._format_time(repo.last_build_finished_at)
            self.last_build_duration = TimeWrapper(repo.last_build_duration, default_format=self.duration_format)

        self.output = dict(
            full_text=formatp(self.format, **vars(self)),
            short_text=self.short_format.format(**vars(self)),
        )
        if self.status_color_map:
            self.output['color'] = self.status_color_map.get(repo.last_build_state, self.color)
        else:
            self.output['color'] = self.color

    def open_build_webpage(self):
        os.popen('xdg-open https://travis-ci.org/{owner}/{repository_name}/builds/{build_id} > /dev/null'
                 .format(owner=self.repo_owner,
                         repository_name=self.repo_name,
                         build_id=self.last_build_id))
