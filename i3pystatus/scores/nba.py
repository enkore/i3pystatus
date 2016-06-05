from i3pystatus.core.util import internet, require
from i3pystatus.scores import ScoresBackend

import copy
import pytz
import time
from datetime import datetime

LIVE_URL = 'http://www.nba.com/gametracker/#/%s/lp'
SCOREBOARD_URL = 'http://www.nba.com/scores'
API_URL = 'http://data.nba.com/data/10s/json/cms/noseason/scoreboard/%04d%02d%02d/games.json'
STANDINGS_URL = 'http://data.nba.com/data/json/cms/%s/league/standings.json'


class NBA(ScoresBackend):
    '''
    Backend to retrieve NBA scores. For usage examples, see :py:mod:`here
    <.scores>`.

    .. rubric:: Available formatters

    * `{home_name}` — Name of home team
    * `{home_city}` — Name of home team's city
    * `{home_abbrev}` — 3-letter abbreviation for home team's city
    * `{home_score}` — Home team's current score
    * `{home_wins}` — Home team's number of wins
    * `{home_losses}` — Home team's number of losses
    * `{home_seed}` — During the playoffs, shows the home team's playoff seed.
      When not in the playoffs, this formatter will be blank.
    * `{home_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the home team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{away_name}` — Name of away team
    * `{away_city}` — Name of away team's city
    * `{away_abbrev}` — 2 or 3-letter abbreviation for away team's city
    * `{away_score}` — Away team's current score
    * `{away_wins}` — Away team's number of wins
    * `{away_losses}` — Away team's number of losses
    * `{away_seed}` — During the playoffs, shows the away team's playoff seed.
      When not in the playoffs, this formatter will be blank.
    * `{away_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the away team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{time_remaining}` — Time remaining in the current quarter/OT period
    * `{quarter}` — Number of the current quarter
    * `{venue}` — Name of arena where game is being played
    * `{start_time}` — Start time of game in system's localtime (supports
      strftime formatting, e.g. `{start_time:%I:%M %p}`)
    * `{overtime}` — If the game ended in overtime, this formatter will show
      ``OT``. If the game ended in regulation, or has not yet completed, this
      formatter will be blank.

    .. rubric:: Team abbreviations

    * **ATL** — Atlanta Hawks
    * **BKN** — Brooklyn Nets
    * **BOS** — Boston Celtics
    * **CHA** — Charlotte Hornets
    * **CHI** — Chicago Bulls
    * **CLE** — Cleveland Cavaliers
    * **DAL** — Dallas Mavericks
    * **DEN** — Denver Nuggets
    * **DET** — Detroit Pistons
    * **GSW** — Golden State Warriors
    * **HOU** — Houston Rockets
    * **IND** — Indiana Pacers
    * **MIA** — Miami Heat
    * **MEM** — Memphis Grizzlies
    * **MIL** — Milwaukee Bucks
    * **LAC** — Los Angeles Clippers
    * **LAL** — Los Angeles Lakers
    * **MIN** — Minnesota Timberwolves
    * **NOP** — New Orleans Pelicans
    * **NYK** — New York Knicks
    * **OKC** — Oklahoma City Thunder
    * **ORL** — Orlando Magic
    * **PHI** — Philadelphia 76ers
    * **PHX** — Phoenix Suns
    * **POR** — Portland Trailblazers
    * **SAC** — Sacramento Kings
    * **SAS** — San Antonio Spurs
    * **TOR** — Toronto Raptors
    * **UTA** — Utah Jazz
    * **WAS** — Washington Wizards
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
        ('team_colors', 'Dictionary mapping team abbreviations to hex color '
                        'codes. If overridden, the passed values will be '
                        'merged with the defaults, so it is not necessary to '
                        'define all teams if specifying this value.'),
        ('date', 'Date for which to display game scores, in **YYYY-MM-DD** '
                 'format. If unspecified, the current day\'s games will be '
                 'displayed starting at 10am Eastern time, with last '
                 'evening\'s scores being shown before then. This option '
                 'exists primarily for troubleshooting purposes.'),
        ('live_url', 'URL string to launch NBA Game Tracker. This value '
                     'should not need to be changed.'),
        ('scoreboard_url', 'Link to the NBA.com scoreboard page. Like '
                           '**live_url**, this value should not need to be '
                           'changed.'),
        ('api_url', 'Alternate URL string from which to retrieve score data. '
                    'Like, **live_url**, this value should not need to be '
                    'changed.'),
        ('standings_url', 'Alternate URL string from which to retrieve team '
                          'standings. Like **live_url**, this value should '
                          'not need to be changed.'),
    )

    required = ()

    _default_colors = {
        'ATL': '#E2383F',
        'BKN': '#DADADA',
        'BOS': '#178D58',
        'CHA': '#00798D',
        'CHI': '#CD1041',
        'CLE': '#FDBA31',
        'DAL': '#006BB7',
        'DEN': '#5593C3',
        'DET': '#207EC0',
        'GSW': '#DEB934',
        'HOU': '#CD1042',
        'IND': '#FFBB33',
        'MIA': '#A72249',
        'MEM': '#628BBC',
        'MIL': '#4C7B4B',
        'LAC': '#ED174C',
        'LAL': '#FDB827',
        'MIN': '#35749F',
        'NOP': '#A78F59',
        'NYK': '#F68428',
        'OKC': '#F05033',
        'ORL': '#1980CB',
        'PHI': '#006BB7',
        'PHX': '#E76120',
        'POR': '#B03037',
        'SAC': '#7A58A1',
        'SAS': '#DADADA',
        'TOR': '#CD112C',
        'UTA': '#4B7059',
        'WAS': '#E51735',
    }

    _valid_teams = [x for x in _default_colors]
    _valid_display_order = ['in_progress', 'final', 'pregame']

    display_order = _valid_display_order
    format_no_games = 'NBA: No games'
    format_pregame = '[{scroll} ]NBA: [{away_favorite} ][{away_seed} ]{away_abbrev} ({away_wins}-{away_losses}) at [{home_favorite} ][{home_seed} ]{home_abbrev} ({home_wins}-{home_losses}) {start_time:%H:%M %Z}'
    format_in_progress = '[{scroll} ]NBA: [{away_favorite} ]{away_abbrev} {away_score}[ ({away_power_play})], [{home_favorite} ]{home_abbrev} {home_score}[ ({home_power_play})] ({time_remaining} {quarter})'
    format_final = '[{scroll} ]NBA: [{away_favorite} ]{away_abbrev} {away_score} ({away_wins}-{away_losses}) at [{home_favorite} ]{home_abbrev} {home_score} ({home_wins}-{home_losses}) (Final[/{overtime}])'
    team_colors = _default_colors
    live_url = LIVE_URL
    scoreboard_url = SCOREBOARD_URL
    api_url = API_URL
    standings_url = STANDINGS_URL

    def check_scores(self):
        self.get_api_date()
        url = self.api_url % (self.date.year, self.date.month, self.date.day)

        response = self.api_request(url)
        game_list = self.get_nested(response,
                                    'sports_content:games:game',
                                    default=[])

        standings_year = self.get_nested(
            response,
            'sports_content:sports_meta:season_meta:standings_season_year',
            default=self.date.year,
        )

        stats_list = self.get_nested(
            self.api_request(self.standings_url % standings_year),
            'sports_content:standings:team',
            default=[],
        )
        team_stats = {}
        for item in stats_list:
            try:
                key = item.pop('abbreviation')
            except KeyError:
                self.logger.debug('Error occurred obtaining team stats',
                                  exc_info=True)
                continue
            team_stats[key] = item.get('team_stats', {})

        self.logger.debug('%s team stats: %s',
                          self.__class__.__name__, team_stats)

        # Convert list of games to dictionary for easy reference later on
        data = {}
        team_game_map = {}
        for game in game_list:
            try:
                id_ = game['game_url']
            except KeyError:
                continue

            try:
                for key in ('home', 'visitor'):
                    team = game[key]['abbreviation'].upper()
                    if team in self.favorite_teams:
                        team_game_map.setdefault(team, []).append(id_)
            except KeyError:
                continue

            data[id_] = game
            # Merge in the team stats, because they are not returned in the
            # initial API request.
            for key in ('home', 'visitor'):
                team = data[id_][key]['abbreviation'].upper()
                data[id_][key].update(team_stats.get(team, {}))

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

        _update('id', 'game_url')
        ret['live_url'] = self.live_url % ret['id']

        status_map = {
            '1': 'pregame',
            '2': 'in_progress',
            '3': 'final',
        }
        period_data = game.get('period_time', {})
        status_code = period_data.get('game_status', '1')
        status = status_map.get(status_code)
        if status is None:
            self.logger.debug('Unknown %s game status code \'%s\'',
                              self.__class__.__name__, status_code)
            status_code = '1'
        ret['status'] = status_map[status_code]

        if ret['status'] in ('in_progress', 'final'):
            period_number = int(period_data.get('period_value', 1))
            total_periods = int(period_data.get('total_periods', 0))
            period_diff = period_number - total_periods
            ret['quarter'] = 'OT' \
                if period_diff == 1 \
                else '%dOT' if period_diff > 1 \
                else self.add_ordinal(period_number)
        else:
            ret['quarter'] = ''

        ret['time_remaining'] = period_data.get('game_clock')
        if ret['time_remaining'] == '':
            ret['time_remaining'] = 'End'
        elif ret['time_remaining'] is None:
            ret['time_remaining'] = ''
        ret['overtime'] = ret['quarter'] if 'OT' in ret['quarter'] else ''

        _update('venue', 'arena')

        for ret_key, game_key in (('home', 'home'), ('away', 'visitor')):
            _update('%s_score' % ret_key, '%s:score' % game_key,
                    callback=self.force_int, default=0)
            _update('%s_city' % ret_key, '%s:city' % game_key)
            _update('%s_name' % ret_key, '%s:nickname' % game_key)
            _update('%s_abbrev' % ret_key, '%s:abbreviation' % game_key)
            if 'playoffs' in game:
                _update('%s_wins' % ret_key, 'playoffs:%s_wins' % game_key,
                        callback=self.force_int, default=0)
                _update('%s_seed' % ret_key, 'playoffs:%s_seed' % game_key,
                        callback=self.force_int, default=0)
            else:
                _update('%s_wins' % ret_key, '%s:wins' % game_key,
                        callback=self.force_int, default=0)
                _update('%s_losses' % ret_key, '%s:losses' % game_key,
                        callback=self.force_int, default=0)
                ret['%s_seed' % ret_key] = ''

        if 'playoffs' in game:
            ret['home_losses'] = ret['away_wins']
            ret['away_losses'] = ret['home_wins']

        # From API data, date is YYYYMMDD, time is HHMM
        game_time_str = '%s%s' % (game.get('date', ''), game.get('time', ''))
        try:
            game_time = datetime.strptime(game_time_str, '%Y%m%d%H%M')
        except ValueError as exc:
            # Log when the date retrieved from the API return doesn't match the
            # expected format (to help troubleshoot API changes), and set an
            # actual datetime so format strings work as expected. The times
            # will all be wrong, but the logging here will help us make the
            # necessary changes to adapt to any API changes.
            self.logger.error(
                'Error encountered determining game time for %s game %s:',
                self.__class__.__name__,
                game['id'],
                exc_info=True
            )
            game_time = datetime.datetime(1970, 1, 1)

        eastern = pytz.timezone('US/Eastern')
        ret['start_time'] = eastern.localize(game_time).astimezone()

        self.logger.debug('Returned %s formatter data: %s',
                          self.__class__.__name__, ret)

        return ret
