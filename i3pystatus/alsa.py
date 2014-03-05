from alsaaudio import Mixer, ALSAAudioError

from i3pystatus import IntervalModule


class ALSA(IntervalModule):

    """
    Shows volume of ALSA mixer. You can also use this for inputs, btw.

    Requires pyalsaaudio

    Available formatters:

    * `{volume}` — the current volume in percent
    * `{muted}` — the value of one of the `muted` or `unmuted` settings
    * `{card}` — the associated soundcard
    * `{mixer}` — the associated ALSA mixer
    """

    interval = 1

    settings = (
        "format",
        ("mixer", "ALSA mixer"),
        ("mixer_id", "ALSA mixer id"),
        ("card", "ALSA sound card"),
        "muted", "unmuted",
        "color_muted", "color",
        "channel"
    )

    muted = "M"
    unmuted = ""
    color_muted = "#AAAAAA"
    color = "#FFFFFF"
    format = "♪: {volume}"
    mixer = "Master"
    mixer_id = 0
    card = 0
    channel = 0

    alsamixer = None
    has_mute = True

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

        self.output = {
            "full_text": self.format.format(**self.fdict),
            "color": self.color_muted if muted else self.color,
        }
