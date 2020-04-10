import copy
import json
import re
import threading
import time
from urllib.request import urlopen

from i3pystatus import IntervalModule, formatp
from i3pystatus.core import ConfigError
from i3pystatus.core.desktop import DesktopNotification
from i3pystatus.core.util import user_open, internet, require

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

API_METHODS_URL = 'https://www.githubstatus.com/api/v2/summary.json'
STATUS_URL = 'https://www.githubstatus.com'
NOTIFICATIONS_URL = 'https://github.com/notifications'
AUTH_URL = 'https://api.github.com/notifications'


class Github(IntervalModule):
    '''
    This module checks the GitHub system status, and optionally the number of
    unread notifications.

    .. versionchanged:: 3.36
        Module now checks system status in addition to unread notifications.

    .. note::
        For notification checking, the following is required:

        - The requests_ module must be installed.
        - Either ``access_token`` (recommended) or ``username`` and
          ``password`` must be used to authenticate to GitHub.

        Using an access token is the recommended authentication method. Click
        here__ to generate a new access token. Fill in the **Token
        description** box, and enable the **notifications** scope by checking
        the appropriate checkbox. Then, click the **Generate token** button.

        .. important::
            An access token is the only supported means of authentication for
            this module, if `2-factor authentication`_ is enabled.

        .. _requests: https://pypi.python.org/pypi/requests
        .. __: https://github.com/settings/tokens/new
        .. _`2-factor authentication`: https://help.github.com/articles/about-two-factor-authentication/

        See here__ for more information on GitHub's authentication API.

        .. __: https://developer.github.com/v3/#authentication

        If you would rather use a username and password pair, you can either
        pass them as arguments when registering the module, or use i3pystatus'
        :ref:`credential management <credentials>` support to store them in a
        keyring. Keep in mind that if you do not pass a ``username`` or
        ``password`` parameter when registering the module, i3pystatus will
        still attempt to retrieve these values from a keyring if the keyring_
        Python module is installed. This could result in i3pystatus aborting
        during startup if it cannot find a usable keyring backend. If you do
        not plan to use credential management at all in i3pystatus, then you
        should either ensure that A) keyring_ is not installed, or B) both
        keyring_ and keyrings.alt_ are installed, to avoid this error.

        .. _keyring: https://pypi.python.org/pypi/keyring
        .. _keyrings.alt: https://pypi.python.org/pypi/keyrings.alt


    .. rubric:: Available formatters

    * `{status}` — Current GitHub status. This formatter can be different
      depending on the current outage status (``none``, ``minor``, ``major``,
      or ``critical``). The content displayed for each of these statuses is
      defined in the **status** config option.
    * `{unread}` — When there are unread notifications, this formatter will
      contain the value of the **unread_marker** marker config option.
      there are no unread notifications, it formatter will be an empty string.
    * `{unread_count}` — The number of unread notifications
      notifications, it will be an empty string.
    * `{update_error}` — When an error is encountered updating this module,
      this formatter will be set to the value of the **update_error**
      config option.

    .. rubric:: Click events

    This module responds to 4 different click events:

    - **Left-click** — Forces an update of the module.
    - **Right-click** — Triggers a desktop notification showing the most recent
      update to the GitHub status. This is useful when the status changes when
      you are away from your computer, so that the updated status can be seen
      without visiting the `GitHub Status Dashboard`_. This click event
      requires **notify_status** to be set to ``True``.
    - **Double left-click** — Opens the GitHub `notifications page`_ in your web
      browser.
    - **Double right-click** — Opens the `GitHub Status Dashboard`_ in your web
      browser.

    .. rubric:: Desktop notifications

    .. versionadded:: 3.36

    If **notify_status** is set to ``True``, a notification will be displayed
    when the status reported by the `GitHub Status API`_ changes.

    If **notify_unread** is set to ``True``, a notification will be displayed
    when new unread notifications are found. Double-clicking the module will
    launch the GitHub notifications dashboard in your browser.

    .. note::
        A notification will be displayed if there was a problem querying the
        `GitHub Status API`_, irrespective of whether or not **notify_status**
        or **notify_unread** is set to ``True``.

    .. rubric:: Example configuration

    The below example enables desktop notifications, enables Pango hinting for
    differently-colored **update_error** and **refresh_icon** text, and alters
    the both the status text and the colors used to visually denote the current
    status level. It also sets the log level to debug, for troubleshooting
    purposes.

    .. code-block:: python

        status.register(
            'github',
            log_level=logging.DEBUG,
            notify_status=True,
            notify_unread=True,
            access_token='0123456789abcdef0123456789abcdef01234567',
            hints={'markup': 'pango'},
            update_error='<span color="#af0000">!</span>',
            refresh_icon='<span color="#ff5f00">⟳</span>',
            status={
                'none': '✓',
                'minor': '!',
                'major': '!!',
                'critical': '!!!',
            },
            colors={
                'none': '#008700',
                'minor': '#d7ff00',
                'major': '#af0000',
                'critical': '#640000',
            },
        )

    .. note::
        Setting debug logging and authenticating with an access token will
        include the access token in the log file, as the notification URL is
        logged at this level.

    .. _`GitHub Status API`: https://www.githubstatus.com/api
    .. _`GitHub Status Dashboard`: https://www.githubstatus.com/
    .. _`notifications page`: https://github.com/notifications

    .. rubric:: Extended string formatting

    .. versionadded:: 3.36

    This module supports the :ref:`formatp <formatp>` extended string format
    syntax. This allows for values to be hidden when they evaluate as False.
    The default ``format`` string value for this module makes use of this
    syntax to conditionally show the value of the ``update_error`` config value
    when the backend encounters an error during an update, but this can also
    be used to only show the number of unread notifications when that number is
    not **0**. The below example would show the unread count as **(3)** when
    there are 3 unread notifications, but would show nothing when there are no
    unread notifications.

    .. code-block:: python

        status.register(
            'github',
            notify_status=True,
            notify_unread=True,
            access_token='0123456789abcdef0123456789abcdef01234567',
            format='{status}[ ({unread_count})][ {update_error}]'
        )
    '''
    settings = (
        ('format', 'format string'),
        ('status', 'Dictionary mapping statuses to the text which represents '
                   'that status type. This defaults to ``GitHub`` for all '
                   'status types.'),
        ('colors', 'Dictionary mapping statuses to the color used to display '
                   'the status text'),
        ('refresh_icon', 'Text to display (in addition to any text currently '
                         'shown by the module) when refreshing the GitHub '
                         'status. **NOTE:** Depending on how quickly the '
                         'update is performed, the icon may not be displayed.'),
        ('update_error', 'Value for the ``{update_error}`` formatter when an '
                         'error is encountered while checking GitHub status'),
        ('keyring_backend', 'alternative keyring backend for retrieving '
                            'credentials'),
        ('username', ''),
        ('password', ''),
        ('access_token', ''),
        ('unread_marker', 'Defines the string that the ``{unread}`` formatter '
                          'shows when there are pending notifications'),
        ('notify_status', 'Set to ``True`` to display a desktop notification '
                          'on status changes'),
        ('notify_unread', 'Set to ``True`` to display a desktop notification '
                          'when new notifications are detected'),
        ('unread_notification_template',
            'String with no more than one ``%d``, which will be replaced by '
            'the number of new unread notifications. Useful for those with '
            'non-English locales who would like the notification to be in '
            'their native language. The ``%d`` can be omitted if desired.'),
        ('api_methods_url', 'URL from which to retrieve the API endpoint URL '
                            'which this module will use to check the GitHub '
                            'Status'),
        ('status_url', 'The URL to the status page (opened when the module is '
                       'double-clicked with the right mouse button'),
        ('notifications_url', 'The URL to the GitHub notifications page '
                              '(opened when the module is double-clicked with '
                              'the left mouse button'),
    )

    # Defaults for module configurables
    _default_status = {
        'none': 'GitHub',
        'minor': 'GitHub',
        'major': 'GitHub',
        'critical': 'GitHub',
    }
    _default_colors = {
        'none': '#28a745',
        'minor': '#dbab09',
        'major': '#e36209',
        'critical': '#dc3545',
    }

    # Module configurables
    format = '{status}[ {unread}][ {update_error}]'
    status = _default_status
    colors = _default_colors
    refresh_icon = '⟳'
    update_error = '!'
    username = ''
    password = ''
    access_token = ''
    unread_marker = '•'
    notify_status = False
    notify_unread = False
    unread_notification_template = 'You have %d new notification(s)'
    api_methods_url = API_METHODS_URL
    status_url = STATUS_URL
    notifications_url = NOTIFICATIONS_URL

    # Global configurables
    interval = 600
    max_error_len = 50
    keyring_backend = None

    # Other
    unread = ''
    unknown_color = None
    unknown_status = '?'
    failed_update = False
    __previous_json = None
    __current_json = None
    new_unread = None
    previous_unread = None
    current_unread = None
    config_error = None
    data = {'status': '',
            'unread': 0,
            'unread_count': '',
            'update_error': ''}
    output = {'full_text': '', 'color': None}

    # Click events
    on_leftclick = ['perform_update']
    on_rightclick = ['show_status_notification']
    on_doubleleftclick = ['launch_notifications_url']
    on_doublerightclick = ['launch_status_url']

    @require(internet)
    def launch_status_url(self):
        self.logger.debug('Launching %s in browser', self.status_url)
        user_open(self.status_url)

    @require(internet)
    def launch_notifications_url(self):
        self.logger.debug('Launching %s in browser', self.notifications_url)
        user_open(self.notifications_url)

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
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

    def update_loop(self):
        try:
            self.perform_update()
            while True:
                with self.condition:
                    self.condition.wait(self.interval)
                self.perform_update()
        except Exception:
            msg = 'Exception in {thread} at {time}, module {name}'.format(
                thread=threading.current_thread().name,
                time=time.strftime('%c'),
                name=self.__class__.__name__,
            )
            self.logger.error(msg, exc_info=True)

    @require(internet)
    def status_api_request(self, url):
        self.logger.debug('Making GitHub Status API request to %s', url)
        try:
            with urlopen(url) as content:
                try:
                    content_type = dict(content.getheaders())['Content-Type']
                    charset = re.search(r'charset=(.*)', content_type).group(1)
                except AttributeError:
                    charset = 'utf-8'
                response_json = content.read().decode(charset).strip()
                if not response_json:
                    self.logger.error('JSON response from %s was blank', url)
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
            if self.__previous_json is None:
                # This is the first time status has been updated since
                # i3pystatus was started. Set self.__previous_json and exit.
                self.__previous_json = response
                return
            if response.get('status', {}).get('description') == self.__previous_json.get('status', {}).get('description'):
                # No change, so no notification
                return
            self.__previous_json = response

        if self.__previous_json is None:
            # The only way this would happen is if we invoked the right-click
            # event before we completed the initial status check.
            return

        self.show_status_notification()

    @staticmethod
    def notify(message):
        return DesktopNotification(title='GitHub', body=message).display()

    def skip_notify(self, message):
        self.logger.debug(
            'Desktop notifications turned off. Skipped notification: %s',
            message
        )
        return False

    def show_status_notification(self):
        message = self.current_status_description
        self.skip_notify(message) \
            if not self.notify_status or (self.previous_status is None and self.current_status == 'none') \
            else self.notify(message)

    def show_unread_notification(self):
        if '%d' not in self.unread_notification_template:
            formatted = self.unread_notification_template
        else:
            try:
                new_unread = len(self.new_unread)
            except TypeError:
                new_unread = 0
            try:
                formatted = self.unread_notification_template % new_unread
            except TypeError as exc:
                self.logger.error(
                    'Failed to format {0!r}: {1}'.format(
                        self.unread_notification_template,
                        exc
                    )
                )
                return False
        return self.skip_notify(formatted) \
            if not self.notify_unread \
            else self.notify(formatted)

    @require(internet)
    def perform_update(self):
        self.output['full_text'] = \
            self.refresh_icon + self.output.get('full_text', '')
        self.failed_update = False

        self.update_status()
        try:
            self.config_error = None
            self.update_unread()
        except ConfigError as exc:
            self.config_error = exc

        self.data['update_error'] = self.update_error \
            if self.failed_update \
            else ''
        self.refresh_display()

    @property
    def current_incidents(self):
        try:
            return self.__current_json['incidents']
        except (KeyError, TypeError):
            return []

    @property
    def previous_incidents(self):
        try:
            return self.__previous_json['incidents']
        except (KeyError, TypeError):
            return []

    @property
    def current_status(self):
        try:
            return self.__current_json['status']['indicator']
        except (KeyError, TypeError):
            return None

    @property
    def previous_status(self):
        try:
            return self.__previous_json['status']['indicator']
        except (KeyError, TypeError):
            return None

    @property
    def current_status_description(self):
        try:
            return self.__current_json['status']['description']
        except (KeyError, TypeError):
            return None

    @require(internet)
    def update_status(self):
        try:
            # Get most recent update
            self.__current_json = self.status_api_request(self.api_methods_url)
            if not self.__current_json:
                self.failed_update = True
                return

            self.data['status'] = self.status.get(self.current_status)
            if self.current_incidents != self.previous_incidents:
                self.show_status_notification()
            self.__previous_json = self.__current_json

        except Exception:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking GitHub status. '
                'Exception follows:', exc_info=True
            )
            self.failed_update = True

    @require(internet)
    def update_unread(self):
        # Reset the new_unread attribute to prevent spurious notifications
        self.new_unread = None

        try:
            if not self.username and not self.password and not self.access_token:
                # Auth not configured
                self.logger.debug(
                    'No auth configured, notifications will not be checked')
                return True

            if not HAS_REQUESTS:
                self.logger.error(
                    'The requests module is required to check GitHub notifications')
                self.failed_update = True
                return False

            self.logger.debug(
                'Checking unread notifications using %s',
                'access token' if self.access_token else 'username/password'
            )

            if self.access_token:
                request_kwargs = {
                    'headers': {
                        'Authorization': 'token {}'.format(self.access_token),
                    },
                }
            else:
                request_kwargs = {
                    'auth': (self.username, self.password),
                }

            self.current_unread = set()
            page_num = 0
            old_unread_url = None
            unread_url = AUTH_URL
            while old_unread_url != unread_url:
                old_unread_url = unread_url
                page_num += 1
                self.logger.debug(
                    'Reading page %d of notifications (%s)',
                    page_num, unread_url
                )
                try:
                    response = requests.get(unread_url, **request_kwargs)
                    self.logger.log(
                        5,
                        'Raw return from GitHub notification check: %s',
                        response.text)
                    unread_data = json.loads(response.text)
                except (requests.ConnectionError, requests.Timeout) as exc:
                    self.logger.error(
                        'Failed to check unread notifications: %s', exc)
                    self.failed_update = True
                    return False
                except json.decoder.JSONDecodeError as exc:
                    self.logger.error('Error loading JSON: %s', exc)
                    self.logger.debug(
                        'JSON text that failed to load: %s', response.text)
                    self.failed_update = True
                    return False

                # Bad credentials or some other error
                if isinstance(unread_data, dict):
                    raise ConfigError(
                        unread_data.get(
                            'message',
                            'Unknown error encountered retrieving unread notifications'
                        )
                    )

                # Update the current count of unread notifications
                self.current_unread.update(
                    [x['id'] for x in unread_data if 'id' in x]
                )

                # Check 'Link' header for next page of notifications
                # (https://tools.ietf.org/html/rfc5988#section-5)
                self.logger.debug('Checking for next page of notifications')
                try:
                    link_header = response.headers['Link']
                except AttributeError:
                    self.logger.error(
                        'No headers present in response. This might be due to '
                        'an API change in the requests module.'
                    )
                    self.failed_update = True
                    continue
                except KeyError:
                    self.logger.debug('Only one page of notifications present')
                    continue
                else:
                    # Process 'Link' header
                    try:
                        links = requests.utils.parse_header_links(link_header)
                    except Exception as exc:
                        self.logger.error(
                            'Failed to parse \'Link\' header: %s', exc
                        )
                        self.failed_update = True
                        continue

                    for link in links:
                        try:
                            link_rel = link['rel']
                            if link_rel != 'next':
                                # Link does not refer to the next page, skip it
                                continue
                            # Set the unread_url so that when we reach the top
                            # of the outer loop, we have a new URL to check.
                            unread_url = link['url']
                            break
                        except TypeError:
                            # Malformed hypermedia link
                            self.logger.warning(
                                'Malformed hypermedia link (%s) in \'Link\' '
                                'header (%s)', link, links
                            )
                            continue
                    else:
                        self.logger.debug('No more pages of notifications remain')

            if self.failed_update:
                return False

            self.data['unread_count'] = len(self.current_unread)
            self.data['unread'] = self.unread_marker \
                if self.data['unread_count'] > 0 \
                else ''

            if self.previous_unread is not None:
                if not self.current_unread.issubset(self.previous_unread):
                    self.new_unread = self.current_unread - self.previous_unread
                    if self.new_unread:
                        self.show_unread_notification()
            self.previous_unread = self.current_unread
            return True
        except ConfigError as exc:
            # This will be caught by the calling function
            raise exc
        except Exception as exc:
            # Don't let an uncaught exception kill the update thread
            self.logger.error(
                'Uncaught error occurred while checking GitHub notifications. '
                'Exception follows:', exc_info=True
            )
            self.failed_update = True
            return False

    def refresh_display(self):
        previous_color = self.output.get('color')
        try:
            color = self.colors.get(
                self.current_status,
                self.unknown_color)
        except TypeError:
            # Shouldn't get here, but this would happen if this function is
            # called before we check the current status for the first time.
            color = previous_color
        self.output = {'full_text': formatp(self.format, **self.data).strip(),
                       'color': color}

    def run(self):
        if self.config_error is not None:
            raise self.config_error
