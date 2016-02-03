from dota2py import api
from i3pystatus import IntervalModule


class Dota2wins(IntervalModule):
    """
    Displays the win/loss ratio of a given Dota account.
    Requires: dota2py
    """

    settings = (
        ("matches", "Number of recent matches to calculate"),
        ("steamid", "Steam ID or username to track"),
        ("steam_api_key", "Steam API key "
            "(http://steamcommunity.com/dev/apikey)"),
        ("good_threshold", "Win percentage (or higher) which you are happy "
            "with"),
        ("bad_threshold", "Win percentage you want to be alerted (difference "
            "between good_threshold and bad_threshold is cautious_threshold)"),
        ("interval", "Update interval (games usually last at least 20 min)."),
        ("good_color", "Color of text while win percentage is above "
            "good_threshold"),
        ("bad_color", "Color of text while win percentage is below "
            "bad_threshold"),
        ("caution_color", "Color of text while win precentage is between good "
            "and bad thresholds"),
        ("screenname", "If set to 'retrieve', requests for the users's "
            "screenname via API calls. Else, use the supplied string as the "
            "user's screename"),
        "format"
    )
    required = ("steamid", "steam_api_key")
    good_color = "#00FF00"     # green
    caution_color = "#FFFF00"  # yellow
    bad_color = "#FF0000"      # red
    good_threshold = 50
    bad_threshold = 45
    matches = 25
    interval = 1800
    screenname = 'retrieve'
    format = "{screenname} {wins}W:{losses}L {win_percent:.2f}%"

    def run(self):
        api.set_api_key(self.steam_api_key)

        if not isinstance(self.steamid, int):
            # find by username
            self.steamid = int(api.get_steam_id(self.steamid)['response']['steamid'])

        hist = api.get_match_history(account_id=self.steamid)['result']
        recent_matches = []
        while len(recent_matches) < self.matches:
            recent_matches.append(hist['matches'].pop(0))

        player_team_per_match = []
        # create a list of tuples where each tuple is:
        # [match_id, bool]
        # The bool will be true if the player is on Radiant and alse if they
        # are on Dire.
        for match in recent_matches:
            this_match = [match['match_id']]
            for player in match['players']:
                # 64bit player ID
                long_id = player['account_id'] + 76561197960265728
                if long_id == self.steamid:
                    if player['player_slot'] < 128:
                        this_match.append(True)
                    else:
                        this_match.append(False)
            player_team_per_match.append(this_match)

        outcomes = []
        for match in player_team_per_match:
            if api.get_match_details(match[0])['result']['radiant_win'] == match[1]:
                outcomes.append(1)
            else:
                outcomes.append(0)

        wins = outcomes.count(1)
        losses = outcomes.count(0)
        win_percent = float(sum(outcomes) / float(len(outcomes))) * 100

        if win_percent >= float(self.good_threshold):
            color = self.good_color
        elif win_percent <= float(self.bad_threshold):
            color = self.bad_color
        else:
            color = self.caution_color

        if self.screenname == 'retrieve':
            from urllib.request import urlopen
            import json
            response = urlopen(
                'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=%s&steamids=%s' %
                (self.steam_api_key, self.steamid))
            screenname = json.loads(bytes.decode(response.read()))['response']['players'][0]['personaname']
        else:
            screenname = self.screenname

        cdict = {
            "screenname": screenname,
            "wins": wins,
            "losses": losses,
            "win_percent": "%.2f" % win_percent,
        }

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
