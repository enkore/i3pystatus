from alsaaudio import Mixer, ALSAAudioError

from i3pystatus import IntervalModule


class ALSA(IntervalModule):
    """
    Shows volume of ALSA mixer. You can also use this for inputs, btw.

    Requires pyalsaaudio

    .. rubric:: Available formatters

    * `{volume}` — the current volume in percent
    * `{muted}` — the value of one of the `muted` or `unmuted` settings
    * `{card}` — the associated soundcard
    * `{mixer}` — the associated ALSA mixer
    """

    interval = 1

    settings = (
        "format",
        ("format_muted", "optional format string to use when muted"),
        ("mixer", "ALSA mixer"),
        ("mixer_id", "ALSA mixer id"),
        ("card", "ALSA sound card"),
        ("increment", "integer percentage of max volume to in/decrement volume on mousewheel"),
        "muted", "unmuted",
        "color_muted", "color",
        "channel"
    )

    muted = "M"
    unmuted = ""
    color_muted = "#AAAAAA"
    color = "#FFFFFF"
    format = "♪: {volume}"
    format_muted = None
    mixer = "Master"
    mixer_id = 0
    card = 0
    channel = 0
    increment = 5

    alsamixer = None
    has_mute = True

    on_scrollup = "increase_volume"
    on_scrolldown = "decrease_volume"
    on_lclick = "switch_mute"
    on_rclick = on_lclick

    def init(self):
        self.create_mixer()
        try:
            self.alsamixer.getmute()
        except ALSAAudioError:
            self.has_mute = False

        self.fdict = {
            "card": self.alsamixer.cardname(),
            "mixer": self.mixer,
        }

    def create_mixer(self):
        self.alsamixer = Mixer(
            control=self.mixer, id=self.mixer_id, cardindex=self.card)

    def run(self):
        self.create_mixer()

        muted = False
        if self.has_mute:
            muted = self.alsamixer.getmute()[self.channel] == 1

        self.fdict["volume"] = self.alsamixer.getvolume()[self.channel]
        self.fdict["muted"] = self.muted if muted else self.unmuted

        if muted and self.format_muted is not None:
            output_format = self.format_muted
        else:
            output_format = self.format

        self.output = {
            "full_text": output_format.format(**self.fdict),
            "color": self.color_muted if muted else self.color,
        }

    def switch_mute(self):
        if self.has_mute:
            muted = self.alsamixer.getmute()[self.channel]
            self.alsamixer.setmute(not muted)

    def increase_volume(self, delta=None):
        vol = self.alsamixer.getvolume()[self.channel]
        self.alsamixer.setvolume(min(100, vol + (delta if delta else self.increment)))

    def decrease_volume(self, delta=None):
        vol = self.alsamixer.getvolume()[self.channel]
        self.alsamixer.setvolume(max(0, vol - (delta if delta else self.increment)))
