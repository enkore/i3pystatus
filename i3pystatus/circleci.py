import os

import dateutil.parser

from circleci.api import Api

from i3pystatus import IntervalModule
from i3pystatus.core.util import TimeWrapper, formatp, internet, require

__author__ = 'chestm007'


class CircleCI(IntervalModule):
    """
    Get current status of circleci builds
    Requires `circleci` `dateutil.parser`

    Formatters:

    * `{repo_slug}`  - repository owner/repository name
    * `{repo_status}` - repository status
    * `{repo_name}` - repository name
    * `{repo_owner}` - repository owner
    * `{last_build_started}` - date of the last finished started
    * `{last_build_duration}` - duration of the last build, not populated with workflows(yet)


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
            'success': '<span color="#00af00">success</span>',
            'running': '<span color="#0000af">running</span>',
            'failed': '<span color="#af0000">failed</span>',
        }

    """

    settings = (
        'format',
        ('circleci_token', 'circleci access token'),
        ('repo_slug', 'repository identifier eg. "enkore/i3pystatus"'),
        ('time_format', 'passed directly to .strftime() for `last_build_started`'),
        ('repo_status_map', 'map representing how to display status'),
        ('duration_format', '`last_build_duration` format string'),
        ('status_color_map', 'color for all text based on status'),
        ('color', 'color for all text not otherwise colored'),
        ('workflow_name', '[WORKFLOWS_ONLY] if specified, monitor this workflows status. if not specified this module '
                          'will default to reporting the status of your last build'),
        ('workflow_branch', '[WORKFLOWS_ONLY] if specified, monitor the workflows in this branch'))

    required = ('circleci_token', 'repo_slug')

    format = '{repo_owner}/{repo_name}-{repo_status} [({last_build_started}({last_build_duration}))]'
    short_format = '{repo_name}-{repo_status}'
    time_format = '%m/%d'
    duration_format = '%m:%S'
    status_color_map = None
    repo_slug = None
    circleci_token = None
    repo_status_map = None
    color = '#DDDDDD'
    workflow_name = None
    workflow_branch = None

    circleci = None

    on_leftclick = 'open_build_webpage'

    def init(self):
        self.repo_status = None
        self.last_build_duration = None
        self.last_build_started = None
        self.repo_owner, self.repo_name = self.repo_slug.split('/')

        self.workflows = self.workflow_name is not None or self.workflow_branch is not None

    def _format_time(self, time):
        _datetime = dateutil.parser.parse(time)
        return _datetime.strftime(self.time_format)

    @require(internet)
    def run(self):
        if self.circleci is None:
            self.circleci = Api(self.circleci_token)

        if self.workflows:
            if self.workflow_branch and not self.workflow_name:
                self.output = dict(
                    full_text='workflow_name must be specified!'
                )
                return

            project = {p['reponame']: p for p in self.circleci.get_projects()}.get(self.repo_name)
            if not self.workflow_branch:
                self.workflow_branch = project.get('default_branch')

            workflow_info = project['branches'].get(self.workflow_branch)['latest_workflows'].get(self.workflow_name)

            self.last_build_started = self._format_time(workflow_info.get('created_at'))
            self.repo_status = workflow_info.get('status')

            self.last_build_duration = ''  # TODO: gather this information once circleCI exposes it

        else:
            self.repo_summary = self.circleci.get_project_build_summary(
                self.repo_owner,
                self.repo_name,
                limit=1)
            if len(self.repo_summary) != 1:
                return
            self.repo_summary = self.repo_summary[0]

            self.repo_status = self.repo_summary.get('status')

            self.last_build_started = self._format_time(self.repo_summary.get('queued_at'))
            try:
                self.last_build_duration = TimeWrapper(
                    self.repo_summary.get('build_time_millis') / 1000,
                    default_format=self.duration_format)
            except TypeError:
                self.last_build_duration = 0

        if self.repo_status_map:
            self.repo_status = self.repo_status_map.get(self.repo_status, self.repo_status)

        self.output = dict(
            full_text=formatp(self.format, **vars(self)),
            short_text=self.short_format.format(**vars(self)),
        )
        if self.status_color_map:
            self.output['color'] = self.status_color_map.get(self.repo_status, self.color)
        else:
            self.output['color'] = self.color

    def open_build_webpage(self):
        if self.repo_summary.get('workflows'):
            url_format = 'workflow-run/{}'.format(self.repo_summary['workflows']['workflow_id'])
        else:
            url_format = 'gh/{repo_owner}/{repo_name}/{job_number}'

        os.popen('xdg-open https:/circleci.com/{} > /dev/null'
                 .format(url_format))
