from i3pystatus.now_playing import NowPlaying


class Spotify(NowPlaying):
    """
    Get Spotify info using dbus interface. Based on `now_playing`_ module.
    """
    player = "spotify"
