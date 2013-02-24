#!/usr/bin/env python
# -*- coding: utf-8 -*-

from i3pystatus import IntervalModule

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

class BatteryChecker(IntervalModule):
    """ 
    This class uses the /proc/acpi/battery interface to check for the
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
        fdict = dict.fromkeys(("remaining", "remaining_hm"), "")

        status = battery.STATUS
        energy_now = battery.ENERGY_NOW
        energy_full = battery.ENERGY_FULL
        power_now = battery.POWER_NOW

        fdict["percentage"] = (energy_now / energy_full) * 100
        fdict["percentage_design"] = (energy_now / battery.ENERGY_FULL_DESIGN) * 100
        fdict["consumption"] = power_now / 1000000

        if status == "Full":
            fdict["status"] = "FULL"
        elif status == "Discharging":
            fdict["status"] = "DIS"
            remaining_time = (energy_now / power_now) * 60
            hours, minutes = map(int, divmod(remaining_time, 60))

            fdict["remaining"] = "{}:{:02}".format(hours, minutes)
            fdict["remaining_hm"] = "{}h {:02}m".format(hours, minutes)
            fdict["remaining_hours"] = hours
            fdict["remaining_mins"] = minutes

            if remaining_time < 15:
                urgent = True
                color = "#ff0000"
        else: # Charging, Unknown etc. (My thinkpad says Unknown if close to fully charged)
            fdict["status"] = "CHR"

        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }

