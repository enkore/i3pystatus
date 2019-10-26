from i3pystatus.core.util import internet, require
from i3pystatus.scores import ScoresBackend

import copy
import json
import pytz
import re
import time
from datetime import datetime
from urllib.request import urlopen

LIVE_URL = 'https://www.nhl.com/gamecenter/%s'
SCOREBOARD_URL = 'https://www.nhl.com/scores'
API_URL = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=%04d-%02d-%02d&endDate=%04d-%02d-%02d&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all&site=en_nhl&teamId='


class NHL(ScoresBackend):
    '''
    Backend to retrieve NHL scores. For usage examples, see :py:mod:`here
    <.scores>`.

    .. rubric:: Available formatters

    * `{home_name}` — Name of home team
    * `{home_city}` — Name of home team's city
    * `{home_abbrev}` — 3-letter abbreviation for home team's city
    * `{home_score}` — Home team's current score
    * `{home_wins}` — Home team's number of wins
    * `{home_losses}` — Home team's number of losses
    * `{home_otl}` — Home team's number of overtime losses
    * `{home_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the home team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{home_empty_net}` — Shows the value from the ``empty_net`` parameter
      when the home team's net is empty.
    * `{away_name}` — Name of away team
    * `{away_city}` — Name of away team's city
    * `{away_abbrev}` — 2 or 3-letter abbreviation for away team's city
    * `{away_score}` — Away team's current score
    * `{away_wins}` — Away team's number of wins
    * `{away_losses}` — Away team's number of losses
    * `{away_otl}` — Away team's number of overtime losses
    * `{away_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the away team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{away_empty_net}` — Shows the value from the ``empty_net`` parameter
      when the away team's net is empty.
    * `{period}` — Current period
    * `{venue}` — Name of arena where game is being played
    * `{start_time}` — Start time of game in system's localtime (supports
      strftime formatting, e.g. `{start_time:%I:%M %p}`)
    * `{overtime}` — If the game ended in overtime or a shootout, this
      formatter will show ``OT`` kor ``SO``. If the game ended in regulation,
      or has not yet completed, this formatter will be blank.

    .. rubric:: Playoffs

    In the playoffs, losses are not important (as the losses will be equal to
    the other team's wins). Therefore, it is a good idea during the playoffs to
    manually set format strings to exclude information on team losses. For
    example:

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.scores import nhl

        status = Status()
        status.register(
            'scores',
            hints={'markup': 'pango'},
            colorize_teams=True,
            favorite_icon='<span size="small" color="#F5FF00">★</span>',
            backends=[
                nhl.NHL(
                    favorite_teams=['CHI'],
                    format_pregame = '[{scroll} ]NHL: [{away_favorite} ]{away_abbrev} ({away_wins}) at [{home_favorite} ]{home_abbrev} ({home_wins}) {start_time:%H:%M %Z}',
                    format_final = '[{scroll} ]NHL: [{away_favorite} ]{away_abbrev} {away_score} ({away_wins}) at [{home_favorite} ]{home_abbrev} {home_score} ({home_wins}) (Final[/{overtime}])',
                ),
            ],
        )

    .. rubric:: Team abbreviations

    * **ANA** — Anaheim Ducks
    * **ARI** — Arizona Coyotes
    * **BOS** — Boston Bruins
    * **BUF** — Buffalo Sabres
    * **CAR** — Carolina Hurricanes
    * **CBJ** — Columbus Blue Jackets
    * **CGY** — Calgary Flames
    * **CHI** — Chicago Blackhawks
    * **COL** — Colorado Avalanche
    * **DAL** — Dallas Stars
    * **DET** — Detroit Red Wings
    * **EDM** — Edmonton Oilers
    * **FLA** — Florida Panthers
    * **LAK** — Los Angeles Kings
    * **MIN** — Minnesota Wild
    * **MTL** — Montreal Canadiens
    * **NJD** — New Jersey Devils
    * **NSH** — Nashville Predators
    * **NYI** — New York Islanders
    * **NYR** — New York Rangers
    * **OTT** — Ottawa Senators
    * **PHI** — Philadelphia Flyers
    * **PIT** — Pittsburgh Penguins
    * **SJS** — San Jose Sharks
    * **STL** — St. Louis Blues
    * **TBL** — Tampa Bay Lightning
    * **TOR** — Toronto Maple Leafs
    * **VAN** — Vancouver Canucks
    * **VGK** — Vegas Golden Knights
    * **WPG** — Winnipeg Jets
    * **WSH** — Washington Capitals
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
        ('empty_net', 'Value for the ``{away_empty_net}`` or '
                      '``{home_empty_net}`` formatter when the net is empty. '
                      'When the net is not empty, these formatters will be '
                      'empty strings.'),
        ('team_colors', 'Dictionary mapping team abbreviations to hex color '
                        'codes. If overridden, the passed values will be '
                        'merged with the defaults, so it is not necessary to '
                        'define all teams if specifying this value.'),
        ('date', 'Date for which to display game scores, in **YYYY-MM-DD** '
                 'format. If unspecified, the current day\'s games will be '
                 'displayed starting at 10am Eastern time, with last '
                 'evening\'s scores being shown before then. This option '
                 'exists primarily for troubleshooting purposes.'),
        ('live_url', 'URL string to launch NHL GameCenter. This value should '
                     'not need to be changed.'),
        ('scoreboard_url', 'Link to the NHL.com scoreboard page. Like '
                           '**live_url**, this value should not need to be '
                           'changed.'),
        ('api_url', 'Alternate URL string from which to retrieve score data. '
                    'Like **live_url**, this value should not need to be '
                    'changed.'),
    )

    required = ()

    _default_colors = {
        'ANA': '#B4A277',
        'ARI': '#AC313A',
        'BOS': '#F6BD27',
        'BUF': '#1568C5',
        'CAR': '#FA272E',
        'CBJ': '#1568C5',
        'CGY': '#D23429',
        'CHI': '#CD0E24',
        'COL': '#9F415B',
        'DAL': '#058158',
        'DET': '#E51937',
        'EDM': '#2F6093',
        'FLA': '#E51837',
        'LAK': '#DADADA',
        'MIN': '#176B49',
        'MTL': '#C8011D',
        'NJD': '#CC0000',
        'NSH': '#FDB71A',
        'NYI': '#F8630D',
        'NYR': '#1576CA',
        'OTT': '#C50B2F',
        'PHI': '#FF690B',
        'PIT': '#FFB81C',
        'SJS': '#007888',
        'STL': '#1764AD',
        'TBL': '#296AD5',
        'TOR': '#296AD5',
        'VAN': '#0454FA',
        'VGK': '#B4975A',
        'WPG': '#1568C5',
        'WSH': '#E51937',
    }

    _valid_teams = [x for x in _default_colors]
    _valid_display_order = ['in_progress', 'final', 'pregame']

    display_order = _valid_display_order
    format_no_games = 'NHL: No games'
    format_pregame = '[{scroll} ]NHL: [{away_favorite} ]{away_abbrev} ({away_wins}-{away_losses}-{away_otl}) at [{home_favorite} ]{home_abbrev} ({home_wins}-{home_losses}-{home_otl}) {start_time:%H:%M %Z}'
    format_in_progress = '[{scroll} ]NHL: [{away_favorite} ]{away_abbrev} {away_score}[ ({away_power_play})][ ({away_empty_net})], [{home_favorite} ]{home_abbrev} {home_score}[ ({home_power_play})][ ({home_empty_net})] ({time_remaining} {period})'
    format_final = '[{scroll} ]NHL: [{away_favorite} ]{away_abbrev} {away_score} ({away_wins}-{away_losses}-{away_otl}) at [{home_favorite} ]{home_abbrev} {home_score} ({home_wins}-{home_losses}-{home_otl}) (Final[/{overtime}])'
    empty_net = 'EN'
    team_colors = _default_colors
    live_url = LIVE_URL
    scoreboard_url = SCOREBOARD_URL
    api_url = API_URL

    @require(internet)
    def check_scores(self):
        self.get_api_date()
        url = self.api_url % (self.date.year, self.date.month, self.date.day,
                              self.date.year, self.date.month, self.date.day)

        game_list = self.get_nested(self.api_request(url),
                                    'dates:0:games',
                                    default=[])

        # Convert list of games to dictionary for easy reference later on
        data = {}
        team_game_map = {}
        for game in game_list:
            try:
                id_ = game['gamePk']
            except KeyError:
                continue

            try:
                for key in ('home', 'away'):
                    team = game['teams'][key]['team']['abbreviation'].upper()
                    if team in self.favorite_teams:
                        team_game_map.setdefault(team, []).append(id_)
            except KeyError:
                continue

            data[id_] = game

        self.interpret_api_return(data, team_game_map)

    def process_game(self, game):
        ret = {}

        self.logger.debug('Processing %s game data: %s',
                          self.__class__.__name__, game)

        linescore = self.get_nested(game, 'linescore', default={})

        ret['id'] = game['gamePk']
        ret['live_url'] = self.live_url % ret['id']
        ret['period'] = self.get_nested(
            linescore,
            'currentPeriodOrdinal')
        ret['time_remaining'] = self.get_nested(
            linescore,
            'currentPeriodTimeRemaining',
            callback=lambda x: x.capitalize())
        ret['venue'] = self.get_nested(
            game,
            'venue:name')

        pp_strength = self.get_nested(linescore, 'powerPlayStrength')

        for team in ('away', 'home'):
            team_data = self.get_nested(game, 'teams:%s' % team, default={})

            if team == 'home':
                ret['venue'] = self.get_nested(team_data, 'venue:name')

            ret['%s_score' % team] = self.get_nested(
                team_data,
                'score',
                callback=self.force_int,
                default=0)
            ret['%s_wins' % team] = self.get_nested(
                team_data,
                'leagueRecord:wins',
                callback=self.force_int,
                default=0)
            ret['%s_losses' % team] = self.get_nested(
                team_data,
                'leagueRecord:losses',
                callback=self.force_int,
                default=0)
            ret['%s_otl' % team] = self.get_nested(
                team_data,
                'leagueRecord:ot',
                callback=self.force_int,
                default=0)

            ret['%s_city' % team] = self.get_nested(
                team_data,
                'team:shortName')
            ret['%s_name' % team] = self.get_nested(
                team_data,
                'team:teamName')
            ret['%s_abbrev' % team] = self.get_nested(
                team_data,
                'team:abbreviation')
            ret['%s_power_play' % team] = self.get_nested(
                linescore,
                'teams:%s:powerPlay' % team,
                callback=lambda x: pp_strength if x and pp_strength != 'Even' else '')
            ret['%s_empty_net' % team] = self.get_nested(
                linescore,
                'teams:%s:goaliePulled' % team,
                callback=lambda x: self.empty_net if x else '')

        if game.get('gameType') == 'P':
            # Calculate wins/losses in current playoff series
            home_rem = ret['home_wins'] % 4
            away_rem = ret['away_wins'] % 4

            if ret['home_wins'] == ret['away_wins']:
                if home_rem == 0:
                    # Both teams have multiples of 4 wins, so series has no
                    # completed games.
                    ret['home_wins'] = ret['away_wins'] = 0
                else:
                    ret['home_wins'] = home_rem
                    ret['away_wins'] = away_rem
            elif ret['home_wins'] > ret['away_wins']:
                ret['home_wins'] = 4 if home_rem == 0 else home_rem
                ret['away_wins'] = away_rem
            else:
                ret['away_wins'] = 4 if away_rem == 0 else away_rem
                ret['home_wins'] = home_rem

            # Series losses are the other team's wins
            ret['home_losses'] = ret['away_wins']
            ret['away_losses'] = ret['home_wins']

        ret['status'] = self.get_nested(
            game,
            'status:abstractGameState',
            callback=lambda x: x.lower().replace(' ', '_'))

        if ret['status'] == 'live':
            ret['status'] = 'in_progress'
        elif ret['status'] == 'final':
            ret['overtime'] = self.get_nested(
                linescore,
                'currentPeriodOrdinal',
                callback=lambda x: x if 'OT' in x or x == 'SO' else '')
        elif ret['status'] != 'in_progress':
            ret['status'] = 'pregame'

        # Game time is in UTC, ISO format, thank the FSM
        # Ex. 2016-04-02T17:00:00Z
        game_time_str = game.get('gameDate', '')
        try:
            game_time = datetime.strptime(game_time_str, '%Y-%m-%dT%H:%M:%SZ')
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
            game_time = datetime.datetime(1970, 1, 1)

        ret['start_time'] = pytz.utc.localize(game_time).astimezone()

        self.logger.debug('Returned %s formatter data: %s',
                          self.__class__.__name__, ret)

        return ret
