import dateutil.parser

from datetime import timedelta, datetime
from travispy import TravisPy

from i3pystatus import IntervalModule

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
    time_format = '%m/%d'

    format = '[{repo_owner}/{repo_name}-{repo_status} ({last_build_finished}({last_build_duration}))]'
    settings = (
        'format',
        ('github_token', 'github personal access token'),
        ('repo_slug', 'repository identifier eg. "enkore/i3pystatus"'),
        ('time_format', 'passed directly to .strftime()'))

    def init(self):
        self.repo_status = None
        self.last_build_duration = None
        self.last_build_finished = None
        self.repo_owner, self.repo_name = self.repo_slug.split('/')
        self.travis = TravisPy.github_auth(self.github_token)

    def _format_time(self, time):
        _datetime = dateutil.parser.parse(time)
        return _datetime.strftime(self.time_format)

    @staticmethod
    def _format_duration(duration):
        sec = timedelta(seconds=int(duration))
        d = datetime(1, 1, 1) + sec
        out = str(d.day - 1) + 'd' if d.day > 1 else ''
        if d.hour > 0:
            out += str(d.hour) + 'h'
        if d.minute > 0:
            out += str(d.minute) + 'm'
        if d.second > 0:
            out += str(d.second) + 's'
        return out

    def run(self):
        repo = self.travis.repo(self.repo_slug)
        self.last_build_finished = self._format_time(repo.last_build_finished_at)
        self.last_build_duration = self._format_duration(repo.last_build_duration)
        self.repo_status = repo.last_build_state
        self.output = dict(full_text=self.format.format(**vars(self)))
