import threading
import math

from i3pystatus import Module
from gi.repository import Playerctl, GLib


class Spotify(Module):

    """
    This class shows information from Spotify.

    Left click will toggle pause/play of the current song.
    Right click will skip the song.

    Dependent on Playerctl ( https://github.com/acrisci/playerctl ) and GLib
    """

    format = "{artist} - {title}"
    color = "#ffffff"

    settings = (
        ("format", "Format string. {artist}, {title}, {album}, {volume}, and {length} are available for output."),
        ("color", "color of the output"),
    )

    def main_loop(self):
        """ Mainloop blocks so we thread it."""
        self.player = Playerctl.Player()
        self.player.on('metadata', self.on_track_change)
        main = GLib.MainLoop()
        main.run()

    def init(self):
        try:
            t = threading.Thread(target=self.main_loop)
            t.daemon = True
            t.start()
        except Exception as e:
            self.output = {
                "full_text": "Error creating new thread!",
                "color"    : "#FF0000"
            }

    def on_track_change(self, player, e):
        artist = player.get_artist()
        title = player.get_title()
        album = player.get_album()
        volume = player.props.volume

        time = e["mpris:length"] / 60.0e6
        minutes = math.floor(time)
        seconds = round(time % 1 * 60)
        if seconds < 10:
            seconds = "0" + str(seconds)
        length = "{}:{}".format(minutes, seconds)

        self.output = {
            "full_text": self.format.format(
                artist=artist, title=title,
                album=album, length=length,
                volume=volume),
            "color": self.color
        }

    def on_leftclick(self):
        self.player.play_pause()

    def on_rightclick(self):
        self.player.next()
