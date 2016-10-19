import math
from i3pystatus import formatp
from i3pystatus import IntervalModule

import gi
gi.require_version('Playerctl', '1.0')  # nopep8
from gi.repository import Playerctl, GLib


class Spotify(IntervalModule):
    """
    Gets Spotify (or any supported player) info using playerctl

    .. rubric:: Available formatters

    * `{status}` — current status icon (paused/playing/stopped)
    * `{length}` — total song duration (mm:ss format)
    * `{artist}` — artist
    * `{title}` — title
    * `{album}` — album
    """

    settings = (
        ('format', 'formatp string'),
        ('format_not_running', 'Text to show if player is not running'),
        ('color', 'The color of the text'),
        ('color_not_running',
            'The color of the text, when player is not running'),
        ('status', 'Dictionary mapping status to output'),
        ('player_name',
            'Name of music player, use `playerctl -l` with player running'
            'to get. If None, tries to autodetect.'),
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
        'stopped': '■',
    }
    player_name = None

    on_leftclick = 'playpause'
    on_rightclick = 'next_song'
    on_upscroll = 'next_song'
    on_downscroll = 'previous_song'

    def _get_length(self, metadata):
        try:
            time = dict(metadata)["mpris:length"] / 60.0e6
            minutes = math.floor(time)
            seconds = round(time % 1 * 60)
            if seconds < 10:
                seconds = "0" + str(seconds)
            length = "{}:{}".format(minutes, seconds)
        except KeyError:
            length = ""

        return length

    def get_info(self, player):
        """gets player track info from playerctl"""

        result = {
            "status": "",
            "artist": "",
            "title": "",
            "album": "",
            "length": "",
        }

        status = player.props.status
        if status:
            result["status"] = self.status.get(status.lower(), None)
            result["artist"] = player.get_artist()
            result["title"] = player.get_title()
            result["album"] = player.get_album()
            result["length"] = self._get_length(player.props.metadata)

        return result

    def run(self):
        """Main statement, executes all code every interval"""

        try:
            self.player = Playerctl.Player(player_name=self.player_name)
            data = self.get_info(self.player)

            self.output = {"full_text": formatp(self.format, **data),
                           "color": self.color}
        except GLib.Error:
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
