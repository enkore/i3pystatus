from i3pystatus.core.util import internet, require
from i3pystatus.scores import ScoresBackend

import copy
import json
import pytz
import re
import time
from datetime import datetime
from urllib.request import urlopen

LIVE_URL = 'http://mlb.mlb.com/mlb/gameday/index.jsp?gid=%s'
SCOREBOARD_URL = 'http://m.mlb.com/scoreboard'
API_URL = 'http://gd2.mlb.com/components/game/mlb/year_%04d/month_%02d/day_%02d/miniscoreboard.json'


class MLB(ScoresBackend):
    '''
    Backend to retrieve MLB scores. For usage examples, see :py:mod:`here
    <.scores>`.

    .. rubric:: Available formatters

    * `{home_name}` — Name of home team
    * `{home_city}` — Name of home team's city
    * `{home_abbrev}` — 2 or 3-letter abbreviation for home team's city
    * `{home_score}` — Home team's current score
    * `{home_wins}` — Home team's number of wins
    * `{home_losses}` — Home team's number of losses
    * `{home_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the home team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{away_name}` — Name of away team
    * `{away_city}` — Name of away team's city
    * `{away_abbrev}` — 2 or 3-letter abbreviation for away team's city
    * `{away_score}` — Away team's current score
    * `{away_wins}` — Away team's number of wins
    * `{away_losses}` — Away team's number of losses
    * `{away_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the away team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{top_bottom}` — Displays the value of either ``inning_top`` or
      ``inning_bottom`` based on whether the game is in the top or bottom of an
      inning.
    * `{inning}` — Current inning
    * `{outs}` — Number of outs in current inning
    * `{venue}` — Name of ballpark where game is being played
    * `{start_time}` — Start time of game in system's localtime (supports
      strftime formatting, e.g. `{start_time:%I:%M %p}`)
    * `{delay}` — Reason for delay, if game is currently delayed. Otherwise,
      this formatter will be blank.
    * `{postponed}` — Reason for postponement, if game has been postponed.
      Otherwise, this formatter will be blank.
    * `{extra_innings}` — When a game lasts longer than 9 innings, this
      formatter will show that number of innings. Otherwise, it will blank.

    .. rubric:: Team abbreviations

    * **ARI** — Arizona Diamondbacks
    * **ATL** — Atlanta Braves
    * **BAL** — Baltimore Orioles
    * **BOS** — Boston Red Sox
    * **CHC** — Chicago Cubs
    * **CIN** — Cincinnati Reds
    * **CLE** — Cleveland Indians
    * **COL** — Colorado Rockies
    * **CWS** — Chicago White Sox
    * **DET** — Detroit Tigers
    * **HOU** — Houston Astros
    * **KC** — Kansas City Royals
    * **LAA** — Los Angeles Angels of Anaheim
    * **LAD** — Los Angeles Dodgers
    * **MIA** — Miami Marlins
    * **MIL** — Milwaukee Brewers
    * **MIN** — Minnesota Twins
    * **NYY** — New York Yankees
    * **NYM** — New York Mets
    * **OAK** — Oakland Athletics
    * **PHI** — Philadelphia Phillies
    * **PIT** — Pittsburgh Pirates
    * **SD** — San Diego Padres
    * **SEA** — Seattle Mariners
    * **SF** — San Francisco Giants
    * **STL** — St. Louis Cardinals
    * **TB** — Tampa Bay Rays
    * **TEX** — Texas Rangers
    * **TOR** — Toronto Blue Jays
    * **WSH** — Washington Nationals
    '''
    interval = 300

    settings = (
        ('favorite_teams', 'List of abbreviations of favorite teams. Games '
                           'for these teams will appear first in the scroll '
                           'list. A detailed description of how games are '
                           'ordered can be found '
                           ':ref:`here <scores-game-order>`.'),
        ('all_games', 'If set to ``True``, all games will be present in '
                      'the scroll list. If set to ``False``, then only '
                      'games from **favorite_teams** will be present in '
                      'the scroll list.'),
        ('display_order', 'When **all_games** is set to ``True``, this '
                          'option will dictate the order in which games from '
                          'teams not in **favorite_teams** are displayed'),
        ('format_no_games', 'Format used when no tracked games are scheduled '
                            'for the current day (does not support formatter '
                            'placeholders)'),
        ('format_pregame', 'Format used when the game has not yet started'),
        ('format_in_progress', 'Format used when the game is in progress'),
        ('format_final', 'Format used when the game is complete'),
        ('format_postponed', 'Format used when the game has been postponed'),
        ('format_suspended', 'Format used when the game has been suspended'),
        ('inning_top', 'Value for the ``{top_bottom}`` formatter when game '
                       'is in the top half of an inning'),
        ('inning_bottom', 'Value for the ``{top_bottom}`` formatter when game '
                          'is in the bottom half of an inning'),
        ('team_colors', 'Dictionary mapping team abbreviations to hex color '
                        'codes. If overridden, the passed values will be '
                        'merged with the defaults, so it is not necessary to '
                        'define all teams if specifying this value.'),
        ('date', 'Date for which to display game scores, in **YYYY-MM-DD** '
                 'format. If unspecified, the current day\'s games will be '
                 'displayed starting at 10am Eastern time, with last '
                 'evening\'s scores being shown before then. This option '
                 'exists primarily for troubleshooting purposes.'),
        ('live_url', 'Alternate URL string to launch MLB Gameday. This value '
                     'should not need to be changed'),
        ('scoreboard_url', 'Link to the MLB.com scoreboard page. Like '
                           '**live_url**, this value should not need to be '
                           'changed.'),
        ('api_url', 'Alternate URL string from which to retrieve score data. '
                    'Like **live_url*** this value should not need to be '
                    'changed.'),
    )

    required = ()

    _default_colors = {
        'ARI': '#A71930',
        'ATL': '#CE1141',
        'BAL': '#DF4601',
        'BOS': '#BD3039',
        'CHC': '#004EC1',
        'CIN': '#C6011F',
        'CLE': '#E31937',
        'COL': '#5E5EB6',
        'CWS': '#DADADA',
        'DET': '#FF6600',
        'HOU': '#EB6E1F',
        'KC': '#0046DD',
        'LAA': '#BA0021',
        'LAD': '#005A9C',
        'MIA': '#00A3E0',
        'MIL': '#0747CC',
        'MIN': '#D31145',
        'NYY': '#0747CC',
        'NYM': '#FF5910',
        'OAK': '#006659',
        'PHI': '#E81828',
        'PIT': '#FFCC01',
        'SD': '#285F9A',
        'SEA': '#2E8B90',
        'SF': '#FD5A1E',
        'STL': '#B53B30',
        'TB': '#8FBCE6',
        'TEX': '#C0111F',
        'TOR': '#0046DD',
        'WSH': '#C70003',
    }

    _valid_teams = [x for x in _default_colors]
    _valid_display_order = ['in_progress', 'suspended', 'final', 'postponed', 'pregame']

    display_order = _valid_display_order
    format_no_games = 'MLB: No games'
    format_pregame = '[{scroll} ]MLB: [{away_favorite} ]{away_abbrev} ({away_wins}-{away_losses}) at [{home_favorite} ]{home_abbrev} ({home_wins}-{home_losses}) {start_time:%H:%M %Z}[ ({delay} Delay)]'
    format_in_progress = '[{scroll} ]MLB: [{away_favorite} ]{away_abbrev} {away_score}, [{home_favorite} ]{home_abbrev} {home_score} ({top_bottom} {inning}, {outs} Out)[ ({delay} Delay)]'
    format_final = '[{scroll} ]MLB: [{away_favorite} ]{away_abbrev} {away_score} ({away_wins}-{away_losses}) at [{home_favorite} ]{home_abbrev} {home_score} ({home_wins}-{home_losses}) (Final[/{extra_innings}])'
    format_postponed = '[{scroll} ]MLB: [{away_favorite} ]{away_abbrev} ({away_wins}-{away_losses}) at [{home_favorite} ]{home_abbrev} ({home_wins}-{home_losses}) (PPD: {postponed})'
    format_suspended = '[{scroll} ]MLB: [{away_favorite} ]{away_abbrev} {away_score} ({away_wins}-{away_losses}) at [{home_favorite} ]{home_abbrev} {home_score} ({home_wins}-{home_losses}) (Suspended: {suspended})'
    inning_top = 'Top'
    inning_bottom = 'Bot'
    team_colors = _default_colors
    live_url = LIVE_URL
    scoreboard_url = SCOREBOARD_URL
    api_url = API_URL

    @require(internet)
    def check_scores(self):
        self.get_api_date()
        url = self.api_url % (self.date.year, self.date.month, self.date.day)

        game_list = self.get_nested(self.api_request(url),
                                    'data:games:game',
                                    default=[])
        if not isinstance(game_list, list):
            # When only one game is taking place during a given day, the game
            # data is just a single dict containing that game's data, rather
            # than a list of dicts. Encapsulate the single game dict in a list
            # to make it process correctly in the loop below.
            game_list = [game_list]

        # Convert list of games to dictionary for easy reference later on
        data = {}
        team_game_map = {}
        for game in game_list:
            try:
                id_ = game['id']
            except (KeyError, TypeError):
                continue

            try:
                for team in (game['home_name_abbrev'], game['away_name_abbrev']):
                    team = team.upper()
                    if team in self.favorite_teams:
                        team_game_map.setdefault(team, []).append(id_)
            except KeyError:
                continue

            data[id_] = game

        self.interpret_api_return(data, team_game_map)

    def process_game(self, game):
        ret = {}

        def _update(ret_key, game_key=None, callback=None, default='?'):
            ret[ret_key] = self.get_nested(game,
                                           game_key or ret_key,
                                           callback=callback,
                                           default=default)

        self.logger.debug('Processing %s game data: %s',
                          self.__class__.__name__, game)

        for key in ('id', 'venue'):
            _update(key)

        for key in ('inning', 'outs'):
            _update(key, callback=self.force_int, default=0)

        ret['live_url'] = self.live_url % game['gameday_link']

        for team in ('home', 'away'):
            _update('%s_wins' % team, '%s_win' % team,
                    callback=self.force_int)
            _update('%s_losses' % team, '%s_loss' % team,
                    callback=self.force_int)
            _update('%s_score' % team, '%s_team_runs' % team,
                    callback=self.force_int, default=0)

            _update('%s_abbrev' % team, '%s_name_abbrev' % team)
            for item in ('city', 'name'):
                _update('%s_%s' % (team, item), '%s_team_%s' % (team, item))

        try:
            ret['status'] = game.get('status').lower().replace(' ', '_')
        except AttributeError:
            # During warmup ret['status'] may be a dictionary. Treat these as
            # pregame
            ret['status'] = 'pregame'

        for key in ('delay', 'postponed', 'suspended'):
            ret[key] = ''

        if ret['status'] == 'delayed_start':
            ret['status'] = 'pregame'
            ret['delay'] = game.get('reason', 'Unknown')
        elif ret['status'] == 'delayed':
            ret['status'] = 'in_progress'
            ret['delay'] = game.get('reason', 'Unknown')
        elif ret['status'] == 'postponed':
            ret['postponed'] = game.get('reason', 'Unknown Reason')
        elif ret['status'] == 'suspended':
            ret['suspended'] = game.get('reason', 'Unknown Reason')
        elif ret['status'] in ('game_over', 'completed_early'):
            ret['status'] = 'final'
        elif ret['status'] not in ('in_progress', 'final'):
            ret['status'] = 'pregame'

        try:
            inning = game.get('inning', '0')
            ret['extra_innings'] = inning \
                if ret['status'] == 'final' and int(inning) != 9 \
                else ''
        except ValueError:
            ret['extra_innings'] = ''

        top_bottom = game.get('top_inning')
        ret['top_bottom'] = self.inning_top if top_bottom == 'Y' \
            else self.inning_bottom if top_bottom == 'N' \
            else ''

        time_zones = {
            'PT': 'US/Pacific',
            'MT': 'US/Mountain',
            'CT': 'US/Central',
            'ET': 'US/Eastern',
        }
        game_tz = pytz.timezone(
            time_zones.get(
                game.get('time_zone', 'ET'),
                'US/Eastern'
            )
        )

        date_and_time = []
        if 'resume_time_date' in game and game['resume_time_date']:
            date_and_time.append(game['resume_time_date'])
        elif 'time_date' in game and game['time_date']:
            date_and_time.append(game['time_date'])
        else:
            keys = ('original_date', 'time')
            if all(key in game for key in keys):
                for key in keys:
                    if game[key]:
                        date_and_time.append(game[key])
        if 'resume_ampm' in game and game['resume_ampm']:
            date_and_time.append(game['resume_ampm'])
        elif 'ampm' in game and game['ampm']:
            date_and_time.append(game['ampm'])

        game_time_str = ' '.join(date_and_time)

        try:
            game_time = datetime.strptime(game_time_str, '%Y/%m/%d %I:%M %p')
        except ValueError as exc:
            # Log when the date retrieved from the API return doesn't match the
            # expected format (to help troubleshoot API changes), and set an
            # actual datetime so format strings work as expected. The times
            # will all be wrong, but the logging here will help us make the
            # necessary changes to adapt to any API changes.
            self.logger.error(
                'Error encountered determining %s game time for game %s:',
                self.__class__.__name__,
                game['id'],
                exc_info=True
            )
            game_time = datetime(1970, 1, 1)

        ret['start_time'] = game_tz.localize(game_time).astimezone()

        self.logger.debug('Returned %s formatter data: %s',
                          self.__class__.__name__, ret)

        return ret
