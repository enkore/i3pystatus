from urllib.request import urlopen
import json
from i3pystatus import IntervalModule


class LastFM(IntervalModule):
    """
    Displays currently playing song as reported by last.fm. Get your API key
    from http://www.last.fm/api.
    """

    settings = (
        ("apikey", "API key used to make calls to last.fm."),
        ("user", "Name of last.fm user to track."),
        ("playing_format", "Output format when a song is playing"),
        ("stopped_format", "Output format when nothing is playing"),
        "playing_color",
        "stopped_color",
        "interval",
    )
    required = ("apikey", "user")
    playing_color = 'FFFFFF'
    stopped_color = '000000'
    interval = 5
    playing_format = "{artist} - {track}"
    stopped_format = ""

    def run(self):
        apiurl = 'http://ws.audioscrobbler.com/2.0/'
        uri = '?method=user.getrecenttracks'\
              '&user=%s&api_key=%s' \
              '&format=json&'\
              'limit=1' % (self.user, self.apikey)
        content = urlopen(apiurl + uri).read()
        responsestr = content.decode('utf-8')
        response = json.loads(responsestr)

        try:
            track = response['recenttracks']['track'][0]
            if track['@attr']['nowplaying'] == 'true':
                cdict = {
                    "artist": track['artist']['#text'],
                    "track": track['name'],
                    "album": track['album']['#text'],
                }

            self.data = cdict
            self.output = {
                "full_text": self.playing_format.format(**cdict),
                "color": self.playing_color
            }
        except KeyError:
            self.output = {
                "full_text": self.stopped_format,
                "color": self.stopped_color
            }
