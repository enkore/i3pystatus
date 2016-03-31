from i3pystatus import IntervalModule, formatp

import datetime
import math

import decimal
import os

from i3pystatus.core.util import TimeWrapper

dec = decimal.Decimal


class MoonPhase(IntervalModule):
    """
    Available Formatters

    status: Allows for mapping of current moon phase
    - New Moon:
    - Waxing Crescent:
    - First Quarter:
    - Waxing Gibbous:
    - Full Moon:
    - Waning Gibbous:
    - Last Quarter:
    - Waning Crescent:

    """

    settings = (
        "format",
        ("status", "Current moon phase"),
        ("illum", "Percentage that is illuminated"),
        ("color", "Set color"),
    )

    format = "{illum} {status}"

    interval = 60 * 60 * 2  # every 2 hours

    status = {
        "New Moon": "NM",
        "Waxing Crescent": "WaxCres",
        "First Quarter": "FQ",
        "Waxing Gibbous": "WaxGib",
        "Full Moon": "FM",
        "Waning Gibbous": "WanGib",
        "Last Quarter": "LQ",
        "Waning Crescent": "WanCres",
    }

    color = {
        "New Moon": "#00BDE5",
        "Waxing Crescent": "#138DD8",
        "First Quarter": "#265ECC",
        "Waxing Gibbous": "#392FBF",
        "Full Moon": "#4C00B3",
        "Waning Gibbous": "#871181",
        "Last Quarter": "#C32250",
        "Waning Crescent": "#FF341F",
    }

    def pos(now=None):
        days_in_second = 86400

        now = datetime.datetime.now()
        difference = now - datetime.datetime(2001, 1, 1)

        days = dec(difference.days) + (dec(difference.seconds) / dec(days_in_second))
        lunarCycle = dec("0.20439731") + (days * dec("0.03386319269"))

        return lunarCycle % dec(1)

    def current_phase(self):

        lunarCycle = self.pos()

        index = (lunarCycle * dec(8)) + dec("0.5")
        index = math.floor(index)

        return {
            0: "New Moon",
            1: "Waxing Crescent",
            2: "First Quarter",
            3: "Waxing Gibbous",
            4: "Full Moon",
            5: "Waning Gibbous",
            6: "Last Quarter",
            7: "Waning Crescent",
        }[int(index) & 7]

    def illum(self):
        phase = 0
        lunarCycle = float(self.pos()) * 100

        if lunarCycle > 50:
            phase = 100 - lunarCycle
        else:
            phase = lunarCycle * 2

        return phase

    def run(self):
        fdict = {
            "status": self.status[self.current_phase()],
            "illum": self.illum(),
        }
        self.data = fdict
        self.output = {
            "full_text": formatp(self.format, **fdict),
            "color": self.color[self.current_phase()],
        }
