from alsaaudio import Mixer, ALSAAudioError
from math import exp, log, log10, ceil, floor

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
        "channel",
        ("map_volume", "volume display/setting as in AlsaMixer. increment option is ignored then.")
    )

    muted = "M"
    unmuted = ""
    color_muted = "#AAAAAA"
    color = "#FFFFFF"
    format = "♪: {volume}"
    format_muted = None
    mixer = "Master"
    mixer_id = 0
    card = -1
    channel = 0
    increment = 5

    map_volume = False

    alsamixer = None
    has_mute = True

    on_upscroll = "increase_volume"
    on_downscroll = "decrease_volume"
    on_leftclick = "switch_mute"
    on_rightclick = on_leftclick

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

        self.dbRng = self.alsamixer.getrange()

        self.dbMin = self.dbRng[0]
        self.dbMax = self.dbRng[1]

    def create_mixer(self):
        self.alsamixer = Mixer(
            control=self.mixer, id=self.mixer_id, cardindex=self.card)

    def run(self):
        self.create_mixer()

        muted = False
        if self.has_mute:
            muted = self.alsamixer.getmute()[self.channel] == 1

        self.fdict["volume"] = self.get_cur_volume()
        self.fdict["muted"] = self.muted if muted else self.unmuted
        self.fdict["db"] = self.get_db()

        if muted and self.format_muted is not None:
            output_format = self.format_muted
        else:
            output_format = self.format

        self.data = self.fdict
        self.output = {
            "full_text": output_format.format(**self.fdict),
            "color": self.color_muted if muted else self.color,
        }

    def switch_mute(self):
        if self.has_mute:
            muted = self.alsamixer.getmute()[self.channel]
            self.alsamixer.setmute(not muted)

    def get_cur_volume(self):
        if self.map_volume:
            dbCur = self.get_db() * 100.0
            dbMin = self.dbMin * 100.0
            dbMax = self.dbMax * 100.0

            dbCur_norm = self.exp10((dbCur - dbMax) / 6000.0)
            dbMin_norm = self.exp10((dbMin - dbMax) / 6000.0)

            vol = (dbCur_norm - dbMin_norm) / (1 - dbMin_norm)
            vol = int(round(vol * 100, 0))

            return vol
        else:
            return self.alsamixer.getvolume()[self.channel]

    def get_new_volume(self, direction):
        if direction == "inc":
            volume = (self.fdict["volume"] + 1) / 100
        elif direction == "dec":
            volume = (self.fdict["volume"] - 1) / 100

        dbMin = self.dbMin * 100
        dbMax = self.dbMax * 100

        dbMin_norm = self.exp10((dbMin - dbMax) / 6000.0)

        vol = volume * (1 - dbMin_norm) + dbMin_norm

        if direction == "inc":
            dbNew = min(self.dbMax, ceil(((6000.0 * log10(vol)) + dbMax) / 100))
        elif direction == "dec":
            dbNew = max(self.dbMin, floor(((6000.0 * log10(vol)) + dbMax) / 100))

        volNew = int(round(self.map_db(dbNew, self.dbMin, self.dbMax, 0, 100), 0))

        return volNew

    def increase_volume(self, delta=None):
        if self.map_volume:
            vol = self.get_new_volume("inc")

            self.alsamixer.setvolume(vol)
        else:
            vol = self.alsamixer.getvolume()[self.channel]
            self.alsamixer.setvolume(min(100, vol + (delta if delta else self.increment)))

    def decrease_volume(self, delta=None):
        if self.map_volume:
            vol = self.get_new_volume("dec")

            self.alsamixer.setvolume(vol)
        else:
            vol = self.alsamixer.getvolume()[self.channel]
            self.alsamixer.setvolume(max(0, vol - (delta if delta else self.increment)))

    def get_db(self):
        db = (((self.dbMax - self.dbMin) / 100) * self.alsamixer.getvolume()[self.channel]) + self.dbMin
        db = int(round(db, 0))

        return db

    def map_db(self, value, dbMin, dbMax, volMin, volMax):
        dbRange = dbMax - dbMin
        volRange = volMax - volMin

        volScaled = float(value - dbMin) / float(dbRange)

        return volMin + (volScaled * volRange)

    def exp10(self, x):
        return exp(x * log(10))
