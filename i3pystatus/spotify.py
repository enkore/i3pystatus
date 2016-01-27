import math
from i3pystatus import formatp
from i3pystatus import IntervalModule
from gi.repository import Playerctl


class Spotify(IntervalModule):
    """
    Gets Spotify info using playerctl

    .. rubric:: Available formatters

    * `{status}` — current status icon (paused/playing)
    * `{length}` — total song duration (mm:ss format)
    * `{artist}` — artist
    * `{title}` — title
    * `{album}` — album
    """

    settings = (
        ('format', 'formatp string'),
        ('format_not_running', 'Text to show if cmus is not running'),
        ('color', 'The color of the text'),
        ('color_not_running', 'The color of the text, when cmus is not running'),
        ('status', 'Dictionary mapping status to output'),
    )

    # default settings
    color = '#ffffff'
    color_not_running = '#ffffff'
    format = '{status} {length} {artist} - {title}'
    format_not_running = 'Not running'
    interval = 1
    status = {
        'paused': '▷',
        'playing': '▶',
    }

    on_leftclick = 'playpause'
    on_rightclick = 'next_song'
    on_upscroll = 'next_song'
    on_downscroll = 'previous_song'

    def get_info(self, player):
        """gets spotify track info from playerctl"""

        artist = player.get_artist()
        title = player.get_title()
        album = player.get_album()
        status = player.props.status

        # gets the length of spotify through the metadata command
        length = ""

        # stores the metadata and checks if it is valid
        metadata = player.props.metadata
        if metadata is not None:
            # math to convert the number stored in mpris:length to a human readable format
            time = dict(metadata)["mpris:length"] / 60.0e6
            minutes = math.floor(time)
            seconds = round(time % 1 * 60)
            if seconds < 10:
                seconds = "0" + str(seconds)
            length = "{}:{}".format(minutes, seconds)

        # sets length to an empty string if it does not exist for whatever reason. This should usually not happen
        else:
            length = ""

        # returns a dictionary of all spotify data
        return {"artist": artist, "title": title, "album": album, "status": status, "length": length}

    def run(self):
        """Main statement, executes all code every interval"""

        # tries to create player object and get data from player
        try:
            self.player = Playerctl.Player()

            response = self.get_info(self.player)

            # creates a dictionary of the spotify data captured
            fdict = {
                'status': self.status[response['status'].lower()],
                'title': response["title"],
                'album': response.get('album', ''),
                'artist': response.get('artist', ''),
                'length': response.get('length', 0),
            }
            self.data = fdict
            self.output = {"full_text": formatp(self.format, **fdict),
                           "color": self.color}

        # outputs the not running string if spotify is closed
        except:
            self.output = {"full_text": self.format_not_running,
                           "color": self.color_not_running}
            if hasattr(self, "data"):
                del self.data

    def playpause(self):
        """Pauses and plays spotify"""
        self.player.play_pause()

    def next_song(self):
        """skips to the next song"""
        self.player.next()

    def previous_song(self):
        """Plays the previous song"""
        self.player.previous()
