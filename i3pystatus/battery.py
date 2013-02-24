#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import IntervalModule
from .core.util import PrefixedKeyDict

class Battery:
    """
    Simple interface to /sys/class/power_supply/BATx/uevent

    The data from uevent is transformed into attributes of this class, stripping
    their prefix. (i.e. POWER_SUPPLY_NAME becomes the NAME attribute).

    Numbers are automatically converted to floats. Strings are stripped.
    """

    @staticmethod
    def lchop(string, prefix="POWER_SUPPLY_"):
        if string.startswith(prefix):
            return string[len(prefix):]
        return string

    @staticmethod
    def convert(value):
        return float(value) if value.isdecimal() else value.strip()

    def __init__(self, file):
        self.parse(file)

    def parse(self, file):
        with open(file, "r") as file:
            for line in file:
                self.parse_line(line.strip())

    def parse_line(self, line):
        key, value = line.split("=", 2)

        setattr(self, self.lchop(key), self.convert(value))

class RemainingCalculator:
    def __init__(self, energy, power):
        self.remaining_time = (energy / power) * 60
        self.hours, self.minutes = map(int, divmod(self.remaining_time, 60))

    def get_dict(self, prefix):
        d = PrefixedKeyDict(prefix)
        d.update({
            "str": "{}:{:02}".format(self.hours, self.minutes),
            "hm": "{}h:{:02}m".format(self.hours, self.minutes),
            "hours": self.hours,
            "mins": self.minutes,
        })
        return d

class BatteryChecker(IntervalModule):
    """ 
    This class uses the /sys/class/power_supply/…/uevent interface to check for the
    battery status
    """
    
    settings = ("battery_ident", "format")
    battery_ident = "BAT0"
    format = "{status} {remaining}"

    def init(self):
        self.base_path = "/sys/class/power_supply/{0}/uevent".format(self.battery_ident)

    def run(self):
        urgent = False
        color = "#ffffff"

        battery = Battery(self.base_path)
        fdict = dict.fromkeys(("remaining_str", "remaining_hm"), "")

        status = battery.STATUS
        energy_now = battery.ENERGY_NOW
        energy_full = battery.ENERGY_FULL
        power_now = battery.POWER_NOW

        fdict["percentage"] = (energy_now / energy_full) * 100
        fdict["percentage_design"] = (energy_now / battery.ENERGY_FULL_DESIGN) * 100
        fdict["consumption"] = power_now / 1000000

        if not power_now:
            return

        if status == "Full":
            fdict["status"] = "FULL"
        else:
            if status == "Discharging":
                fdict["status"] = "DIS"
                remaining = RemainingCalculator(energy_now, power_now)

                if remaining.remaining_time < 15:
                    urgent = True
                    color = "#ff0000"
            else: # Charging, Unknown etc. (My thinkpad says Unknown if close to fully charged)
                fdict["status"] = "CHR"
                remaining = RemainingCalculator(energy_full-energy_now, power_now)
            fdict.update(remaining.get_dict("remaining_"))

        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }

