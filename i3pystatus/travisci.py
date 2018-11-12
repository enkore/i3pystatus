import dateutil.parser

from datetime import timedelta
from travispy import TravisPy

from i3pystatus import IntervalModule
from i3pystatus.core.util import TimeWrapper

__author__ = 'chestm007'


class TravisCI(IntervalModule):
    """
    Get current status of travis builds
    Requires `travispy`

    Formatters:

    * `{repo_slug}`  - repository owner/repository name
    * `{repo_status}` - repository status
    * `{repo_name}` - repository name
    * `{repo_owner}` - repository owner
    * `{last_build_finished}` - <
    * `{last_build_duration}` - <
    """

    settings = (
        'format',
        ('github_token', 'github personal access token'),
        ('repo_slug', 'repository identifier eg. "enkore/i3pystatus"'),
        ('time_format', 'passed directly to .strftime() for `last_build_finished`'),
        ('duration_format', '`last_build_duration` format string'))

    required = ('github_token', 'repo_slug')

    format = '[{repo_owner}/{repo_name}-{repo_status} ({last_build_finished}({last_build_duration}))]'
    time_format = '%m/%d'
    duration_format = '%m:%S'

    def init(self):
        self.repo_status = None
        self.last_build_duration = None
        self.last_build_finished = None
        self.repo_owner, self.repo_name = self.repo_slug.split('/')
        self.travis = TravisPy.github_auth(self.github_token)

    def _format_time(self, time):
        _datetime = dateutil.parser.parse(time)
        return _datetime.strftime(self.time_format)

    def run(self):
        repo = self.travis.repo(self.repo_slug)
        self.last_build_finished = self._format_time(repo.last_build_finished_at)
        self.last_build_duration = str(timedelta)
        self.last_build_duration = TimeWrapper(repo.last_build_duration, default_format=self.duration_format)
        self.repo_status = repo.last_build_state
        self.output = dict(full_text=self.format.format(**vars(self)))
