from i3pystatus.mpris import Mpris


class Spotify(Mpris):
    """
    Get Spotify info using dbus interface. Based on `mpris`_ module.
    """
    player_name = "spotify"
