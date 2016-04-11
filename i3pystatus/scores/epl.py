from i3pystatus.core.util import internet, require
from i3pystatus.scores import ScoresBackend

import copy
import pytz
import time
from collections import namedtuple
from datetime import datetime

LIVE_URL = 'http://live.premierleague.com/#/gameweek/%s/matchday/%s/match/%s'
CONTEXT_URL = 'http://live.premierleague.com/syndicationdata/context.json'
SCOREBOARD_URL = 'http://live.premierleague.com/'
API_URL = 'http://live.premierleague.com/syndicationdata/competitionId=%s/seasonId=%s/gameWeekId=%s/scores.json'
STATS_URL = 'http://live.premierleague.com/syndicationdata/competitionId=%s/seasonId=%s/matchDayId=%s/league-table.json'
MATCH_DETAILS_URL = 'http://live.premierleague.com/syndicationdata/competitionId=%s/seasonId=%s/matchDayId=%s/matchId=%s/match-details.json'

MATCH_STATUS_PREGAME = 1
MATCH_STATUS_IN_PROGRESS = 2
MATCH_STATUS_FINAL = 3
MATCH_STATUS_HALFTIME = 4


class EPL(ScoresBackend):
    '''
    Backend to retrieve scores from the English Premier League. For usage
    examples, see :py:mod:`here <.scores>`.

    .. rubric:: Promotion / Relegation

    Due to promotion/relegation, the **team_colors** configuration will
    eventuall become out of date. When this happens, it will be necessary to
    manually set the colors for the newly-promoted teams until the source for
    this module is updated. An example of setting colors for newly promoted
    teams can be seen below:

    .. code-block:: python

        from i3pystatus import Status
        from i3pystatus.scores import epl

        status = Status()

        status.register(
            'scores',
            hints={'markup': 'pango'},
            colorize_teams=True,
            backends=[
                epl.EPL(
                    teams=['LIV'],
                    team_colors={
                        'ABC': '#1D78CA',
                        'DEF': '#8AFEC3',
                        'GHI': '#33FA6D',
                    },
                ),
            ],
        )

        status.run()

    .. rubric:: Available formatters

    * `{home_name}` — Name of home team (e.g. **Tottenham Hotspur**)
    * `{home_name_short}` — Shortened team name (e.g. **Spurs**)
    * `{home_abbrev}` — 2 or 3-letter abbreviation for home team's city (e.g.
       **TOT**)
    * `{home_score}` — Home team's current score
    * `{home_wins}` — Home team's number of wins
    * `{home_losses}` — Home team's number of losses
    * `{home_draws}` — Home team's number of draws
    * `{home_points}` — Home team's number of standings points
    * `{home_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the home team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{away_name}` — Name of away team (e.g. **Manchester United**)
    * `{away_name_short}` — Name of away team's city (e.g. **Man Utd**)
    * `{away_abbrev}` — 2 or 3-letter abbreviation for away team's name (e.g.
       **MUN**)
    * `{away_score}` — Away team's current score
    * `{away_wins}` — Away team's number of wins
    * `{away_losses}` — Away team's number of losses
    * `{away_draws}` — Away team's number of draws
    * `{away_points}` — Away team's number of standings points
    * `{away_favorite}` — Displays the value for the :py:mod:`.scores` module's
      ``favorite`` attribute, if the away team is one of the teams being
      followed. Otherwise, this formatter will be blank.
    * `{minute}` — Current minute of game when in progress
    * `{start_time}` — Start time of game in system's localtime (supports
      strftime formatting, e.g. `{start_time:%I:%M %p}`)

    .. rubric:: Team abbreviations

    * **ARS** — Arsenal
    * **AVL** — Aston Villa
    * **BOU** — Bournemouth
    * **CHE** — Chelsea
    * **CRY** — Crystal Palace
    * **EVE** — Everton
    * **LEI** — Leicester City
    * **LIV** — Liverpool
    * **MCI** — Manchester City
    * **MUN** — Manchester United
    * **NEW** — Newcastle United
    * **NOR** — Norwich City
    * **SOU** — Southampton
    * **STK** — Stoke City
    * **SUN** — Sunderland Association
    * **SWA** — Swansea City
    * **TOT** — Tottenham Hotspur
    * **WAT** — Watford
    * **WBA** — West Bromwich Albion
    * **WHU** — West Ham United
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
                 'format. If unspecified, the date will be determined by '
                 'the return value of an API call to the **context_url**. '
                 'Due to API limitations, the date can presently only be '
                 'overridden to another date in the current week. This '
                 'option exists primarily for troubleshooting purposes.'),
        ('live_url', 'URL string to launch EPL Live Match Centre. This value '
                     'should not need to be changed.'),
        ('scoreboard_url', 'Link to the EPL scoreboard page. Like '
                           '**live_url**, this value should not need to be '
                           'changed.'),
        ('api_url', 'Alternate URL string from which to retrieve score data. '
                    'Like **live_url**, this value should not need to be '
                    'changed.'),
        ('stats_url', 'Alternate URL string from which to retrieve team '
                      'statistics. Like **live_url**, this value should not '
                      'need to be changed.'),
        ('match_details_url', 'Alternate URL string from which to retrieve '
                              'match details. Like **live_url**, this value '
                              'should not need to be changed.'),
    )

    required = ()

    _default_colors = {
        'ARS': '#ED1B22',
        'AVL': '#94BEE5',
        'BOU': '#CB0B0F',
        'CHE': '#195FAF',
        'CRY': '#195FAF',
        'EVE': '#004F9E',
        'LEI': '#304FB6',
        'LIV': '#D72129',
        'MCI': '#74B2E0',
        'MUN': '#DD1921',
        'NEW': '#06B3EB',
        'NOR': '#00A651',
        'SOU': '#DB1C26',
        'STK': '#D81732',
        'SUN': '#BC0007',
        'SWA': '#B28250',
        'TOT': '#DADADA',
        'WAT': '#E4D500',
        'WBA': '#B43C51',
        'WHU': '#9DE4FA',
    }

    _valid_display_order = ['in_progress', 'final', 'pregame']

    display_order = _valid_display_order
    format_no_games = 'EPL: No games'
    format_pregame = '[{scroll} ]EPL: [{away_favorite} ]{away_abbrev} ({away_points}, {away_wins}-{away_losses}-{away_draws}) at [{home_favorite} ]{home_abbrev} ({home_points}, {home_wins}-{home_losses}-{home_draws}) {start_time:%H:%M %Z}'
    format_in_progress = '[{scroll} ]EPL: [{away_favorite} ]{away_abbrev} {away_score}[ ({away_power_play})], [{home_favorite} ]{home_abbrev} {home_score}[ ({home_power_play})] ({minute})'
    format_final = '[{scroll} ]EPL: [{away_favorite} ]{away_abbrev} {away_score} ({away_points}, {away_wins}-{away_losses}-{away_draws}) at [{home_favorite} ]{home_abbrev} {home_score} ({home_points}, {home_wins}-{home_losses}-{home_draws}) (Final)'
    team_colors = _default_colors
    context_url = CONTEXT_URL
    live_url = LIVE_URL
    scoreboard_url = SCOREBOARD_URL
    api_url = API_URL
    stats_url = STATS_URL
    match_details_url = MATCH_DETAILS_URL

    def get_api_date(self):
        # NOTE: We're not really using this date for EPL API calls, but we do
        # need it to allow for a 'date' param to override which date we use for
        # scores.
        if self.date is not None and not isinstance(self.date, datetime):
            try:
                self.date = datetime.strptime(self.date, '%Y-%m-%d')
            except (TypeError, ValueError):
                self.logger.warning('Invalid date \'%s\'', self.date)

        if self.date is None:
            self.date = datetime.strptime(self.context.date, '%Y%m%d')

    def get_context(self):
        response = self.api_request(self.context_url)
        context_tuple = namedtuple(
            'Context',
            ('competition', 'date', 'game_week', 'match_day', 'season')
        )
        self.context = context_tuple(
            *[
                response.get(x, '')
                for x in ('competitionId', 'currentDay', 'gameWeekId',
                          'matchDayId', 'seasonId')
            ]
        )

    def get_team_stats(self):
        ret = {}
        url = self.stats_url % (self.context.competition,
                                self.context.season,
                                self.context.match_day)
        for item in self.api_request(url).get('Data', []):
            try:
                key = item.pop('TeamCode')
            except KeyError:
                self.logger.debug('Error occurred obtaining %s team stats',
                                  self.__class__.__name__,
                                  exc_info=True)
                continue
            ret[key] = item
        return ret

    def get_minute(self, data, id_):
        match_status = data[id_].get('StatusId', MATCH_STATUS_PREGAME)
        if match_status == MATCH_STATUS_HALFTIME:
            return 'Halftime'
        if match_status == MATCH_STATUS_IN_PROGRESS:
            url = self.match_details_url % (self.context.competition,
                                            self.context.season,
                                            data[id_].get('MatchDayId', ''),
                                            id_)
            try:
                response = self.api_request(url)
                return '%s\'' % response['Data']['Minute']
            except (KeyError, TypeError):
                return '?\''
        else:
            return '?\''

    def check_scores(self):
        self.get_context()
        self.get_api_date()

        url = self.api_url % (self.context.competition,
                              self.context.season,
                              self.context.game_week)

        for item in self.api_request(url).get('Data', []):
            if item.get('Key', '') == self.date.strftime('%Y%m%d'):
                game_list = item.get('Scores', [])
                break
        else:
            game_list = []
        self.logger.debug('game_list = %s', game_list)

        team_stats = self.get_team_stats()

        # Convert list of games to dictionary for easy reference later on
        data = {}
        team_game_map = {}
        for game in game_list:
            try:
                id_ = game['Id']
            except KeyError:
                continue

            try:
                for key in ('HomeTeam', 'AwayTeam'):
                    team = game[key]['Code'].upper()
                    if team in self.favorite_teams:
                        team_game_map.setdefault(team, []).append(id_)
            except KeyError:
                continue

            data[id_] = game
            # Merge in the team stats, because they are not returned in the
            # initial API request.
            for key in ('HomeTeam', 'AwayTeam'):
                team = game[key]['Code'].upper()
                data[id_][key]['Stats'] = team_stats.get(team, {})
            # Add the minute, if applicable
            data[id_]['Minute'] = self.get_minute(data, id_)

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

        _update('id', 'Id')
        _update('minute', 'Minute')
        ret['live_url'] = self.live_url % (self.context.game_week,
                                           self.context.match_day,
                                           ret['id'])

        status_map = {
            MATCH_STATUS_PREGAME: 'pregame',
            MATCH_STATUS_IN_PROGRESS: 'in_progress',
            MATCH_STATUS_FINAL: 'final',
            MATCH_STATUS_HALFTIME: 'in_progress',
        }
        status_code = game.get('StatusId')
        if status_code is None:
            self.logger.debug('%s game %s is missing StatusId',
                              self.__class__.__name__, ret['id'])
            status_code = 1
        ret['status'] = status_map[status_code]

        for ret_key, game_key in (('home', 'HomeTeam'), ('away', 'AwayTeam')):
            _update('%s_score' % ret_key, '%s:Score' % game_key, default=0)
            _update('%s_name' % ret_key, '%s:Name' % game_key)
            _update('%s_name_short' % ret_key, '%s:ShortName' % game_key)
            _update('%s_abbrev' % ret_key, '%s:Code' % game_key)
            _update('%s_wins' % ret_key, '%s:Stats:Won' % game_key, default=0)
            _update('%s_losses' % ret_key, '%s:Stats:Lost' % game_key)
            _update('%s_draws' % ret_key, '%s:Stats:Drawn' % game_key)
            _update('%s_points' % ret_key, '%s:Stats:Points' % game_key)

        try:
            game_time = datetime.strptime(
                game.get('DateTime', ''),
                '%Y-%m-%dT%H:%M:%S'
            )
        except ValueError as exc:
            # Log when the date retrieved from the API return doesn't match the
            # expected format (to help troubleshoot API changes), and set an
            # actual datetime so format strings work as expected. The times
            # will all be wrong, but the logging here will help us make the
            # necessary changes to adapt to any API changes.
            self.logger.error(
                'Error encountered determining game time for %s game %s:',
                self.__class__.__name__,
                ret['id'],
                exc_info=True
            )
            game_time = datetime.datetime(1970, 1, 1)

        london = pytz.timezone('Europe/London')
        ret['start_time'] = london.localize(game_time).astimezone()

        self.logger.debug('Returned %s formatter data: %s',
                          self.__class__.__name__, ret)

        return ret
