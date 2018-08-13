from i3pystatus import IntervalModule
import soco


class Sonos(IntervalModule):
    """
    Controls and displays information from Sonos devices.

    A devices is found by IP, by name, or automatically if no IP or name is \
    supplied.

    .. rubric:: Available formatters

    * `{player_name}` — player name
    * `{volume}` — volume from 0 to 100
    * `{muted}` — "M" if muted, else ""
    * `{title}` — the title of the current song
    * `{artist}` — the artist of the current song
    * `{album}` — the album of the current song
    * `{duration}` — duration of the current song (%M:%S)
    * `{position}` — position in the current song (%M:%S)
    * `{state}` — Playing, Paused, Stopped

    Requires: soco (can be installed using pip)
    """

    ip = None
    name = None
    format = "{state}: {artist} - {title} [{muted}{volume:.0f}%]"
    color = "#FFFFFF"
    format_no_music = "No music"
    color_no_music = "#888888"
    format_no_connection = "No connection"
    color_no_connection = "#888888"
    hide_no_connection = False

    interval = 1

    settings = (
        ("ip", "Speaker IP address."),
        ("name", "Speaker name (used if no IP is given)."),
        ("format", "Format used when playing or paused."),
        ("color", "Color used when playing or paused."),
        ("format_no_music", "Format used when stopped."),
        ("color_no_music", "Color used when stopped."),
        ("format_no_connection", "Format used if no player is connected."),
        ("color_no_connection", "Color used if no player is connected."),
        ("hide_no_connection", "Hide output if no player is connected."),
    )

    state_text_map = {
        "PLAYING": "Playing",
        "TRANSITIONING": "Playing",
        "PAUSED_PLAYBACK": "Paused",
        "STOPPED": "Stopped",
    }

    on_leftclick = "play_pause"
    on_upscroll = "incr_vol"
    on_middleclick = "toggle_mute"
    on_downscroll = "decr_vol"
    on_doubleleftclick = "next_song"

    player = None

    def run(self):
        if not self.player:
            if self.ip:
                self.player = soco.SoCo(self.ip)
            elif self.name:
                self.player = soco.discovery.by_name(self.name)
            else:
                self.player = soco.discovery.any_soco()

        if not self.player:
            self.output = self.output_no_connection
            return

        try:
            track_info = self.group_coordinator.get_current_track_info()
            transp_info = self.group_coordinator.get_current_transport_info()
            player_name = self.player.player_name
            muted = self.player.mute
            volume = self.player.volume
        except:
            self.output = self.output_no_connection
            return

        state = transp_info["current_transport_state"]

        cdict = {
            "player_name": player_name,
            "volume": volume,
            "muted": "M" if muted else "",
            "title": track_info["title"],
            "artist": track_info["artist"],
            "album": track_info["album"],
            "duration": track_info["duration"][2:],
            "position": track_info["position"][2:],
            "state": self.state_text_map[state],
        }

        self.data = cdict

        if self.format_no_music is not None and state == "STOPPED":
            self.output = {
                "full_text": self.format_no_music.format(**cdict),
                "color": self.color_no_music
            }
        else:
            self.output = {
                "full_text": self.format.format(**cdict),
                "color": self.color
            }

    @property
    def output_no_connection(self):
        if self.hide_no_connection:
            return None
        else:
            return {
                "full_text": self.format_no_connection,
                "color": self.color_no_connection
            }

    @property
    def group_coordinator(self):
        try:
            return self.player.group.coordinator
        except:
            return None

    def play_pause(self):
        try:
            transp_info = self.group_coordinator.get_current_transport_info()
            state = transp_info["current_transport_state"]
            if state in ["PLAYING", "TRANSITIONING"]:
                self.group_coordinator.pause()
            else:
                self.group_coordinator.play()
        except:
            return

    def incr_vol(self):
        try:
            self.player.volume += 1
        except:
            return

    def decr_vol(self):
        try:
            self.player.volume -= 1
        except:
            return

    def toggle_mute(self):
        try:
            self.player.mute = not self.player.mute
        except:
            return

    def next_song(self):
        try:
            self.group_coordinator.next()
        except:
            return
