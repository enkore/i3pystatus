from i3pystatus import formatp
from i3pystatus import IntervalModule
from i3pystatus.core.util import TimeWrapper

import gi
gi.require_version('Playerctl', '1.0')  # nopep8
from gi.repository import Playerctl


class Spotify(IntervalModule):
    """
    Gets Spotify (or any supported player) info using playerctl

    .. rubric:: Available formatters

    * `{status}` — current status icon (paused/playing/stopped)
    * `{length}` — total song duration, uses TimeWrapper formatting, default format is `%E%l:%M:%S`
    * `{artist}` — artist
    * `{title}` — title
    * `{album}` — album
    """

    settings = (
        ('format', 'formatp string'),
        ('format_not_running', 'Text to show if player is not running'),
        ('color', 'The color of the text'),
        ('color_not_running', 'The color of the text, when player is not running'),
        ('status', 'Dictionary mapping status to output'),
        ('player_name',
            'Name of music player, use `playerctl -l` with player running to get. If None, tries to autodetect.'),
    )

    # default settings
    color = '#ffffff'
    color_not_running = '#ffffff'
    format = '{status} {length} {artist} - {title}'
    format_not_running = 'Not running'
    status = {
        'paused': '▷',
        'playing': '▶',
        'stopped': '■',
    }
    player_name = None

    on_leftclick = 'playpause'
    on_rightclick = 'next_song'
    on_upscroll = 'next_song'
    on_downscroll = 'previous_song'

    def _get_length_in_secs(self, metadata):
        if not metadata:
            return 0
        try:
            time = metadata["mpris:length"] / 1.0e6
            seconds = round(time)
            return seconds
        except KeyError:
            return 0

    def get_formatted_info(self, player):
        """Get player track info from playerctl"""

        result = {
            "status": "",
            "artist": "",
            "title": "",
            "album": "",
            "length": "",
        }

        status = player.props.status
        if status:
            result["status"] = self.status.get(status.lower(), "")
            result["artist"] = player.get_artist()
            result["title"] = player.get_title()
            result["album"] = player.get_album()
            length_in_secs = self._get_length_in_secs(player.props.metadata)
            result["length"] = TimeWrapper(length_in_secs, "%E%l%M:%S")

        return result

    def run(self):
        """Main statement, executes all code every interval"""

        self.player = Playerctl.Player(player_name=self.player_name)
        fdict = self.get_formatted_info(self.player)
        if fdict.get("status", ""):
            self.output = {"full_text": formatp(self.format, **fdict),
                           "color": self.color}
        else:
            self.output = {"full_text": self.format_not_running,
                           "color": self.color_not_running}

    def playpause(self):
        """Pauses and plays player"""
        self.player.play_pause()

    def next_song(self):
        """skips to the next song"""
        self.player.next()

    def previous_song(self):
        """Plays the previous song"""
        self.player.previous()
