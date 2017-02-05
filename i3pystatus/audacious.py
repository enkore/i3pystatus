from .now_playing import NowPlaying
from os import system


class Audacious(NowPlaying):

    on_upscroll = "previous_song"
    on_downscroll = "next_song"
    command = "audtool"
    
    def _audtool_command(self, command):
        system(
            "{0} {1}".format(self.command, command)
        )
    

    def next_song(self):
        self._audtool_command("playlist-advance")

    def previous_song(self):
        self._audtool_command("playlist-reverse")
