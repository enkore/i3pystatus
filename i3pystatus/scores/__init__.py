import copy
import json
import operator
import pytz
import re
import threading
import time
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from i3pystatus import SettingsBase, Module, formatp
from i3pystatus.core.util import user_open, internet, require


class ScoresBackend(SettingsBase):
    settings = ()
    favorite_teams = []
    all_games = True
    date = None
    games = {}
    scroll_order = []
    last_update = 0

    def init(self):
        # Merge the passed team colors with the global ones. A simple length
        # check is sufficient here because i3pystatus.scores.Scores instance
        # will already have checked to see if any invalid teams were specified
        # in team_colors.
        if len(self.team_colors) != len(self._default_colors):
            self.logger.debug(
                'Overriding %s team colors with: %s',
                self.__class__.__name__,
                self.team_colors
            )
            new_colors = copy.copy(self._default_colors)
            new_colors.update(self.team_colors)
            self.team_colors = new_colors
        self.logger.debug('%s team colors: %s',
                          self.__class__.__name__, self.team_colors)

    def api_request(self, url):
        self.logger.debug('Making %s API request to %s',
                          self.__class__.__name__, url)
        try:
            with urlopen(url) as content:
                try:
                    if content.url != url:
                        self.logger.debug('Request to %s was redirected to %s',
                                          url, content.url)
                    content_type = dict(content.getheaders())['Content-Type']
                    mime_type = content_type.split(';')[0].lower()
                    if 'json' not in mime_type:
                        self.logger.debug('Response from %s is not JSON',
                                          content.url)
                        return {}
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
        except HTTPError as exc:
            self.logger.critical(
                'Error %s (%s) making request to %s',
                exc.code, exc.reason, exc.url,
            )
            return {}
        except (ConnectionResetError, URLError) as exc:
            self.logger.critical('Error making request to %s: %s', url, exc)
            return {}

    def get_api_date(self):
        '''
        Figure out the date to use for API requests. Assumes yesterday's date
        if between midnight and 10am Eastern time. Override this function in a
        subclass to change how the API date is calculated.
        '''
        # NOTE: If you are writing your own function to get the date, make sure
        # to include the first if block below to allow for the ``date``
        # parameter to hard-code a date.
        api_date = None
        if self.date is not None and not isinstance(self.date, datetime):
            try:
                api_date = datetime.strptime(self.date, '%Y-%m-%d')
            except (TypeError, ValueError):
                self.logger.warning('Invalid date \'%s\'', self.date)

        if api_date is None:
            utc_time = pytz.utc.localize(datetime.utcnow())
            eastern = pytz.timezone('US/Eastern')
            api_date = eastern.normalize(utc_time.astimezone(eastern))
            if api_date.hour < 10:
                # The scores on NHL.com change at 10am Eastern, if it's before
                # that time of day then we will use yesterday's date.
                api_date -= timedelta(days=1)
        self.date = api_date

    @staticmethod
    def add_ordinal(number):
        try:
            number = int(number)
        except ValueError:
            return number
        if 4 <= number <= 20:
            return '%d%s' % (number, 'th')
        else:
            ord_map = {1: 'st', 2: 'nd', 3: 'rd'}
            return '%d%s' % (number, ord_map.get(number % 10, 'th'))

    @staticmethod
    def force_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def get_nested(self, data, expr, callback=None, default=''):
        if callback is None:
            def callback(x):
                return x
        try:
            for key in expr.split(':'):
                if key.isdigit() and isinstance(data, list):
                    key = int(key)
                data = data[key]
        except (KeyError, IndexError, TypeError):
            self.logger.debug('No %s data found at %s, falling back to %s',
                              self.__class__.__name__, expr, repr(default))
            return default
        return callback(data)

    def interpret_api_return(self, data, team_game_map):
        favorite_games = []
        # Cycle through the followed teams to ensure that games show up in the
        # order of teams being followed.
        for team in self.favorite_teams:
            for id_ in team_game_map.get(team, []):
                if id_ not in favorite_games:
                    favorite_games.append(id_)

        # If all games are being tracked, add any games not from
        # explicitly-followed teams.
        if self.all_games:
            additional_games = [x for x in data if x not in favorite_games]
        else:
            additional_games = []

        # Process the API return data for each tracked game
        self.games = {}
        for game_id in favorite_games + additional_games:
            self.games[game_id] = self.process_game(data[game_id])

        # Favorite games come first
        self.scroll_order = [self.games[x]['id'] for x in favorite_games]

        # For any remaining games being tracked, sort each group by start time
        # and add them to the list
        for status in self.display_order:
            time_map = {
                x: self.games[x]['start_time'] for x in self.games
                if x not in favorite_games and self.games[x]['status'] == status
            }
            sorted_games = sorted(time_map.items(), key=operator.itemgetter(1))
            self.scroll_order.extend([x[0] for x in sorted_games])

        # Reverse map so that we can know the scroll position for a given game
        # by just its ID. This will help us to place the game in its new order
        # when that order changes due to the game changing from one status to
        # another.
        self.scroll_order_revmap = {y: x for x, y in enumerate(self.scroll_order)}


class Scores(Module):
    '''
    This is a generic score checker, which must use at least one configured
    :ref:`score backend <scorebackends>`.

    Followed games can be scrolled through with the mouse/trackpad.
    Left-clicking on the module will refresh the scores, while right-clicking
    it will cycle through the configured backends. Double-clicking the module
    with the left button will launch the league-specific (MLB Gameday / NHL
    GameCenter / etc.) URL for the game. If there is not an active game,
    double-clicking will launch the league-specific scoreboard URL containing
    all games for the current day.

    Double-clicking with the right button will reset the current backend to the
    first game in the scroll list. This is useful for quickly switching back to
    a followed team's game after looking at other game scores.

    Scores for the previous day's games will be shown until 10am Eastern Time
    (US), after which time the current day's games will be shown.

    .. rubric:: Available formatters

    Formatters are set in the backend instances, see the :ref:`scorebackends`
    for more information.

    This module supports the :ref:`formatp <formatp>` extended string format
    syntax. This allows for values to be hidden when they evaluate as False
    (e.g. when a formatter is blank (an empty string). The default values for
    the format strings set in the :ref:`score backends <scorebackends>`
    (``format_pregame``, ``format_in_progress``, etc.) make heavy use of
    formatp, hiding many formatters when they are blank.

    .. rubric:: Usage example

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.scores import mlb, nhl

        status = Status()

        status.register(
            'scores',
            hints={'markup': 'pango'},
            colorize_teams=True,
            favorite_icon='<span size="small" color="#F5FF00">★</span>',
            backends=[
                mlb.MLB(
                    teams=['CWS', 'SF'],
                    format_no_games='No games today :(',
                    inning_top='⬆',
                    inning_bottom='⬇',
                ),
                nhl.NHL(teams=['CHI']),
                nba.NBA(
                    teams=['GSW'],
                    all_games=False,
                ),
                epl.EPL(),
            ],
        )

        status.run()

    To enable colorized team name/city/abbbreviation, ``colorize_teams`` must
    be set to ``True``. This also requires that i3bar is configured to use
    Pango, and that the :ref:`hints <hints>` param is set for the module and
    includes a ``markup`` key, as in the example above. To ensure that i3bar is
    configured to use Pango, the `font param`__ in your i3 config file must
    start with ``pango:``.

    .. __: http://i3wm.org/docs/userguide.html#fonts

    .. _scores-game-order:

    If a ``teams`` param is not specified for the backend, then all games for
    the current day will be tracked, and will be ordered by the start time of
    the game. Otherwise, only games from explicitly-followed teams will be
    tracked, and will be in the same order as listed. If ``ALL`` is part of the
    list, then games from followed teams will be first in the scroll list,
    followed by all remaining games in order of start time.

    Therefore, in the above example, only White Sox and Giants games would be
    tracked, while in the below example all games would be tracked, with
    White Sox and Giants games appearing first in the scroll list and the
    remaining games appearing after them, in order of start time.

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.scores import mlb

        status = Status()

        status.register(
            'scores',
            hints={'markup': 'pango'},
            colorize_teams=True,
            favorite_icon='<span size="small" color="#F5FF00">★</span>',
            backends=[
                mlb.MLB(
                    teams=['CWS', 'SF', 'ALL'],
                    team_colors={
                        'NYM': '#1D78CA',
                    },
                ),
            ],
        )

        status.run()

    .. rubric:: Troubleshooting

    If the module gets stuck during an update (i.e. the ``refresh_icon`` does
    not go away), then the update thread probably encountered a traceback. This
    traceback will (by default) be logged to ``~/.i3pystatus-<pid>`` where
    ``<pid>`` is the PID of the thread. However, it may be more convenient to
    manually set the logfile to make the location of the log data reliable and
    avoid clutter in your home directory. For example:

    .. code-block:: python

        import logging
        from i3pystatus import Status
        from i3pystatus.scores import mlb, nhl

        status = Status(
            logfile='/home/username/var/i3pystatus.log',
        )

        status.register(
            'scores',
            log_level=logging.DEBUG,
            backends=[
                mlb.MLB(
                    teams=['CWS', 'SF'],
                    log_level=logging.DEBUG,
                ),
                nhl.NHL(
                    teams=['CHI'],
                    log_level=logging.DEBUG,
                ),
                nba.NBA(
                    teams=['CHI'],
                    log_level=logging.DEBUG,
                ),
            ],
        )

        status.run()

    .. note::
        The ``log_level`` must be set separately in both the module and the
        backend instances (as shown above), otherwise the backends will
        still use the default log level.
    '''
    interval = 300

    settings = (
        ('backends', 'List of backend instances'),
        ('interval', 'Update interval (in seconds)'),
        ('favorite_icon', 'Value for the ``{away_favorite}`` and '
                          '``{home_favorite}`` formatter when the displayed game '
                          'is being played by a followed team'),
        ('color', 'Color to be used for non-colorized text (defaults to the '
                  'i3bar color)'),
        ('color_no_games', 'Color to use when no games are scheduled for the '
                           'currently-displayed backend (defaults to the '
                           'i3bar color)'),
        ('colorize_teams', 'Dislay team city, name, and abbreviation in the '
                           'team\'s color (as defined in the '
                           ':ref:`backend <scorebackends>`\'s ``team_colors`` '
                           'attribute)'),
        ('scroll_arrow', 'Value used for the ``{scroll}`` formatter to '
                         'indicate that more than one game is being tracked '
                         'for the currently-displayed backend'),
        ('refresh_icon', 'Text to display (in addition to any text currently '
                         'shown by the module) when refreshing scores. '
                         '**NOTE:** Depending on how quickly the update is '
                         'performed, the icon may not be displayed.'),
    )

    backends = []
    favorite_icon = '★'
    color = None
    color_no_games = None
    colorize_teams = False
    scroll_arrow = '⬍'
    refresh_icon = '⟳'

    output = {'full_text': ''}
    game_map = {}
    backend_id = 0

    on_upscroll = ['scroll_game', 1]
    on_downscroll = ['scroll_game', -1]
    on_leftclick = ['check_scores', 'click event']
    on_rightclick = ['cycle_backend', 1]
    on_doubleleftclick = ['launch_web']
    on_doublerightclick = ['reset_backend']

    def init(self):
        if not isinstance(self.backends, list):
            self.backends = [self.backends]

        if not self.backends:
            raise ValueError('At least one backend is required')

        # Initialize each backend's game index
        for index in range(len(self.backends)):
            self.game_map[index] = None

        for backend in self.backends:
            if hasattr(backend, '_valid_teams'):
                for index in range(len(backend.favorite_teams)):
                    # Force team abbreviation to uppercase
                    team_uc = str(backend.favorite_teams[index]).upper()
                    # Check to make sure the team abbreviation is valid
                    if team_uc not in backend._valid_teams:
                        raise ValueError(
                            'Invalid %s team \'%s\'' % (
                                backend.__class__.__name__,
                                backend.favorite_teams[index]
                            )
                        )
                    backend.favorite_teams[index] = team_uc

            for index in range(len(backend.display_order)):
                order_lc = str(backend.display_order[index]).lower()
                # Check to make sure the display order item is valid
                if order_lc not in backend._valid_display_order:
                    raise ValueError(
                        'Invalid %s display_order \'%s\'' % (
                            backend.__class__.__name__,
                            backend.display_order[index]
                        )
                    )
                backend.display_order[index] = order_lc

        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.update_thread, daemon=True)
        self.thread.start()

    def update_thread(self):
        try:
            self.check_scores(force='scheduled')
            while True:
                with self.condition:
                    self.condition.wait(self.interval)
                self.check_scores(force='scheduled')
        except Exception:
            msg = 'Exception in {thread} at {time}, module {name}'.format(
                thread=threading.current_thread().name,
                time=time.strftime('%c'),
                name=self.__class__.__name__,
            )
            self.logger.error(msg, exc_info=True)

    @property
    def current_backend(self):
        return self.backends[self.backend_id]

    @property
    def current_scroll_index(self):
        return self.game_map[self.backend_id]

    @property
    def current_game_id(self):
        try:
            return self.current_backend.scroll_order[self.current_scroll_index]
        except (AttributeError, TypeError):
            return None

    @property
    def current_game(self):
        try:
            return self.current_backend.games[self.current_game_id]
        except KeyError:
            return None

    def scroll_game(self, step=1):
        cur_index = self.current_scroll_index
        if cur_index is None:
            self.logger.debug(
                'Cannot scroll, no tracked {backend} games for '
                '{date:%Y-%m-%d}'.format(
                    backend=self.current_backend.__class__.__name__,
                    date=self.current_backend.date,
                )
            )
        else:
            new_index = (cur_index + step) % len(self.current_backend.scroll_order)
            if new_index != cur_index:
                cur_id = self.current_game_id
                # Don't reference self.current_scroll_index here, we're setting
                # a new value for the data point for which
                # self.current_scroll_index serves as a shorthand.
                self.game_map[self.backend_id] = new_index
                self.logger.debug(
                    'Scrolled from %s game %d (ID: %s) to %d (ID: %s)',
                    self.current_backend.__class__.__name__,
                    cur_index,
                    cur_id,
                    new_index,
                    self.current_backend.scroll_order[new_index],
                )
                self.refresh_display()
            else:
                self.logger.debug(
                    'Cannot scroll, only one tracked {backend} game '
                    '(ID: {id_}) for {date:%Y-%m-%d}'.format(
                        backend=self.current_backend.__class__.__name__,
                        id_=self.current_game_id,
                        date=self.current_backend.date,
                    )
                )

    def cycle_backend(self, step=1):
        if len(self.backends) < 2:
            self.logger.debug(
                'Only one backend (%s) configured, backend cannot be changed',
                self.current_backend.__class__.__name__,
            )
            return
        old = self.backend_id
        # Set the new backend
        self.backend_id = (self.backend_id + step) % len(self.backends)
        self.logger.debug(
            'Changed scores backend from %s to %s',
            self.backends[old].__class__.__name__,
            self.current_backend.__class__.__name__,
        )
        # Display the score for the new backend. This gets rid of lag between
        # when the mouse is clicked and when the new backend is shown, caused
        # by any network latency encountered when updating scores.
        self.refresh_display()
        # Update scores (if necessary) and display them
        self.check_scores()

    def reset_backend(self):
        if self.current_backend.games:
            self.game_map[self.backend_id] = 0
            self.logger.debug(
                'Resetting to first game in %s scroll list (ID: %s)',
                self.current_backend.__class__.__name__,
                self.current_game_id,
            )
            self.refresh_display()
        else:
            self.logger.debug(
                'No %s games, cannot reset to first game in scroll list',
                self.current_backend.__class__.__name__,
            )

    def launch_web(self):
        game = self.current_game
        if game is None:
            live_url = self.current_backend.scoreboard_url
        else:
            live_url = game['live_url']
        self.logger.debug('Launching %s in browser', live_url)
        user_open(live_url)

    @require(internet)
    def check_scores(self, force=False):
        update_needed = False
        if not self.current_backend.last_update:
            update_needed = True
            self.logger.debug(
                'Performing initial %s score check',
                self.current_backend.__class__.__name__,
            )
        elif force:
            update_needed = True
            self.logger.debug(
                '%s score check triggered (%s)',
                self.current_backend.__class__.__name__,
                force
            )
        else:
            update_diff = time.time() - self.current_backend.last_update
            msg = ('Seconds since last %s update (%f) ' %
                   (self.current_backend.__class__.__name__, update_diff))
            if update_diff >= self.interval:
                update_needed = True
                msg += ('meets or exceeds update interval (%d), update '
                        'triggered' % self.interval)
            else:
                msg += ('does not exceed update interval (%d), update '
                        'skipped' % self.interval)
            self.logger.debug(msg)

        if update_needed:
            self.show_refresh_icon()
            cur_id = self.current_game_id
            cur_games = self.current_backend.games.keys()
            self.current_backend.check_scores()
            if cur_games == self.current_backend.games.keys():
                # Set the index to the scroll position of the current game (it
                # may have changed due to this game or other games changing
                # status.
                if cur_id is None:
                    self.logger.debug(
                        'No tracked {backend} games for {date:%Y-%m-%d}'.format(
                            backend=self.current_backend.__class__.__name__,
                            date=self.current_backend.date,
                        )
                    )
                else:
                    cur_pos = self.game_map[self.backend_id]
                    new_pos = self.current_backend.scroll_order_revmap[cur_id]
                    if cur_pos != new_pos:
                        self.game_map[self.backend_id] = new_pos
                        self.logger.debug(
                            'Scroll position for current %s game (%s) updated '
                            'from %d to %d',
                            self.current_backend.__class__.__name__,
                            cur_id,
                            cur_pos,
                            new_pos,
                        )
                    else:
                        self.logger.debug(
                            'Scroll position (%d) for current %s game (ID: %s) '
                            'unchanged',
                            cur_pos,
                            self.current_backend.__class__.__name__,
                            cur_id,
                        )
            else:
                # Reset the index to 0 if there are any tracked games,
                # otherwise set it to None to signify no tracked games for the
                # backend.
                if self.current_backend.games:
                    self.game_map[self.backend_id] = 0
                    self.logger.debug(
                        'Tracked %s games updated, setting scroll position to '
                        '0 (ID: %s)',
                        self.current_backend.__class__.__name__,
                        self.current_game_id
                    )
                else:
                    self.game_map[self.backend_id] = None
                    self.logger.debug(
                        'No tracked {backend} games for {date:%Y-%m-%d}'.format(
                            backend=self.current_backend.__class__.__name__,
                            date=self.current_backend.date,
                        )
                    )
            self.current_backend.last_update = time.time()
        self.refresh_display()

    def show_refresh_icon(self):
        self.output['full_text'] = \
            self.refresh_icon + self.output.get('full_text', '')

    def refresh_display(self):
        if self.current_scroll_index is None:
            output = self.current_backend.format_no_games
            color = self.color_no_games
        else:
            game = copy.copy(self.current_game)

            fstr = str(getattr(
                self.current_backend,
                'format_%s' % game['status']
            ))

            for team in ('home', 'away'):
                abbrev_key = '%s_abbrev' % team
                # Set favorite icon, if applicable
                game['%s_favorite' % team] = self.favorite_icon \
                    if game[abbrev_key] in self.current_backend.favorite_teams \
                    else ''

                if self.colorize_teams:
                    # Wrap in Pango markup
                    color = self.current_backend.team_colors.get(
                        game.get(abbrev_key)
                    )
                    if color is not None:
                        for item in ('abbrev', 'city', 'name', 'name_short'):
                            key = '%s_%s' % (team, item)
                            if key in game:
                                val = '<span color="%s">%s</span>' % (color, game[key])
                                game[key] = val

            game['scroll'] = self.scroll_arrow \
                if len(self.current_backend.games) > 1 \
                else ''

            output = formatp(fstr, **game).strip()

        self.output = {'full_text': output, 'color': self.color}

    def run(self):
        pass
