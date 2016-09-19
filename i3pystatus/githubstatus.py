import copy
import json
import re
import threading
import time
from urllib.request import urlopen

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.desktop import DesktopNotification
from i3pystatus.core.util import user_open, internet, require

API_METHODS_URL = 'https://status.github.com/api.json'


class GitHubStatus(IntervalModule):
    '''
    This module uses the `GitHub Status API`_ to show whether or not there are
    currently any issues with github.com. Clicking the module will force it to
    update, and double-clicking it will launch the `GitHub Status Dashboard`_
    (the URL for the status page can be overriden using the **status_page**
    option).

    .. _`GitHub Status API`: https://status.github.com/api
    .. _`GitHub Status Dashboard`: https://status.github.com

    .. rubric:: Available formatters

    * `{status}` — Current GitHub status. This formatter can be different
      depending on the current status (``good``, ``minor``, or ``major``).
      The content displayed for each of these statuses is defined in the
      **status** config option.
    * `{update_error}` — When an error is encountered updating the GitHub
      status, this formatter will be set to the value of the **update_error**
      config option. Otherwise, this formatter will be an empty string.

    .. rubric:: Desktop notifications

    If **notify** is set to ``True``, then desktop notifications will be
    enabled for this module. A notification will be displayed if there was a
    problem querying the `GitHub Status API`_, and also when the status changes.
    Additionally, right-clicking the module will replay the notification for
    the most recent status change.

    .. rubric:: Example configuration

    The below example enables desktop notifications, enables Pango hinting for
    differently-colored **update_error** and **refresh_icon** text, and alters
    the colors used to visually denote the current status level.

    .. code-block:: python

        status.register(
            'githubstatus',
            notify=True,
            hints={'markup': 'pango'},
            update_error='<span color="#af0000">!</span>',
            refresh_icon='<span color="#ff5f00">⟳</span>',
            colors={
                'good': '#008700',
                'minor': '#d7ff00',
                'major': '#af0000',
            },
        )

    '''

    settings = (
        ('status', 'Dictionary mapping statuses to the text which represents '
                   'that status type'),
        ('colors', 'Dictionary mapping statuses to the color used to display '
                   'the status text'),
        ('refresh_icon', 'Text to display (in addition to any text currently '
                         'shown by the module) when refreshing the GitHub '
                         'status. **NOTE:** Depending on how quickly the '
                         'update is performed, the icon may not be displayed.'),
        ('status_page', 'Page to launch when module is double-clicked'),
        ('notify', 'Set to ``True`` to enable desktop notifications'),
        ('update_error', 'Value for the ``{update_error}`` formatter when an '
                         'error is encountered while checking GitHub status'),
        ('format', 'Format to use for displaying status info'),
    )

    _default_status = {
        'good': 'GitHub',
        'minor': 'GitHub',
        'major': 'GitHub',
    }
    _default_colors = {
        'good': '#00ff00',
        'minor': '#ffff00',
        'major': '#ff0000',
    }

    status = _default_status
    colors = _default_colors
    refresh_icon = '⟳'
    status_page = 'https://status.github.com'
    notify = False
    update_error = '!'
    format = '{status}[ {update_error}]'

    # A color of None == a fallback to the default status bar color
    unknown_color = None
    unknown_status = '?'
    previous_change = None
    current_status = {}

    data = {'status': '', 'update_error': ''}
    output = {'full_text': '', 'color': None}
    interval = 300

    on_leftclick = ['check_status']
    on_rightclick = ['notify_change']
    on_doubleleftclick = ['launch_status_page']

    def init(self):
        if self.status != self._default_status:
            new_status = copy.copy(self._default_status)
            new_status.update(self.status)
            self.status = new_status

        if self.colors != self._default_colors:
            new_colors = copy.copy(self._default_colors)
            new_colors.update(self.colors)
            self.colors = new_colors

        self.logger.debug('status = %s', self.status)
        self.logger.debug('colors = %s', self.colors)

        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.update_thread, daemon=True)
        self.thread.start()

    def update_thread(self):
        try:
            self.check_status()
            while True:
                with self.condition:
                    self.condition.wait(self.interval)
                self.check_status()
        except Exception:
            msg = 'Exception in {thread} at {time}, module {name}'.format(
                thread=threading.current_thread().name,
                time=time.strftime('%c'),
                name=self.__class__.__name__,
            )
            self.logger.error(msg, exc_info=True)

    @require(internet)
    def launch_status_page(self):
        self.logger.debug('Launching %s in browser', self.status_page)
        user_open(self.status_page)

    @require(internet)
    def api_request(self, url):
        self.logger.debug('Making API request to %s', url)
        try:
            with urlopen(url) as content:
                try:
                    content_type = dict(content.getheaders())['Content-Type']
                    charset = re.search(r'charset=(.*)', content_type).group(1)
                except AttributeError:
                    charset = 'utf-8'
                response_json = content.read().decode(charset).strip()
                if not response_json:
                    self.logger.debug('JSON response from %s was blank', url)
                    return {}
                try:
                    response = json.loads(response_json)
                except json.decoder.JSONDecodeError as exc:
                    self.logger.error('Error loading JSON: %s', exc)
                    self.logger.debug('JSON text that failed to load: %s',
                                      response_json)
                    return {}
                self.logger.log(5, 'API response: %s', response)
                return response
        except Exception as exc:
            self.logger.error(
                'Failed to make API request to %s. Exception follows:', url,
                exc_info=True
            )
            return {}

    def detect_status_change(self, response=None):
        if response is not None:
            # Compare last update to current and exit without displaying a
            # notification if one is not needed.
            if self.previous_change is None:
                # This is the first time status has been updated since
                # i3pystatus was started. Set self.previous_change and exit.
                self.previous_change = response
                return
            if response == self.previous_change:
                # No change, so no notification
                return
            self.previous_change = response

        if self.previous_change is None:
            # The only way this would happen is if we invoked the right-click
            # event before we completed the initial status check.
            return

        self.notify_change()

    def notify_change(self):
        message = self.previous_change.get(
            'body',
            'Missing \'body\' param in API response'
        )
        self.display_notification(message)

    def display_notification(self, message):
        if not self.notify:
            self.logger.debug(
                'Skipping notification, desktop notifications turned off'
            )
            return
        DesktopNotification(
            title='GitHub Status',
            body=message).display()

    @require(internet)
    def check_status(self):
        '''
        Check the weather using the configured backend
        '''
        self.output['full_text'] = \
            self.refresh_icon + self.output.get('full_text', '')
        self.query_github()
        if self.current_status:
            # Show desktop notification if status changed (and alerts enabled)
            self.detect_status_change(self.current_status)
        self.refresh_display()

    def query_github(self):
        self.data['update_error'] = ''
        color = None
        try:
            # Get most recent update
            if not hasattr(self, 'last_message_url'):
                self.last_message_url = \
                    self.api_request(API_METHODS_URL)['last_message_url']
            self.current_status = self.api_request(self.last_message_url)
            if not self.current_status:
                self.data['update_error'] = self.update_error
                return

            self.data['status'] = self.status.get(
                self.current_status.get('status'),
                self.unknown_status)
        except Exception:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking GitHub status. '
                'Exception follows:', exc_info=True
            )
            self.data['update_error'] = self.update_error

    def refresh_display(self):
        color = self.colors.get(
            self.current_status.get('status'),
            self.unknown_color)
        self.output = {'full_text': formatp(self.format, **self.data).strip(),
                       'color': color}
        if self.data['update_error']:
            self.display_notification(
                'Error occurred checking GitHub status. See log for details.'
            )

    def run(self):
        pass
