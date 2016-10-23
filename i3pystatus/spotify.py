from i3pystatus.playerctl import Playerctl


class Spotify(Playerctl):
    """
    Get Spotify info using playerctl. Based on `Playerctl`_ module.
    """
    player_name = "spotify"
