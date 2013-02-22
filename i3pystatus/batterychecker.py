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
    
    settings = ("battery_ident",)
    battery_ident = "BAT0"

    def init(self):
        self.base_path = "/sys/class/power_supply/{0}/uevent".format(self.battery_ident)

    def run(self):
        urgent = False
        color = "#ffffff"

        battery = Battery(self.base_path)

        status = battery.STATUS
        energy_now = battery.ENERGY_NOW

        if status == "Full":
            full_text = "fully charged"
        elif status == "Discharging":
            power_now = battery.POWER_NOW
            remaining_time_secs = (energy_now / power_now) * 3600
            hours, remainder = divmod(remaining_time_secs, 3600)
            minutes, seconds = divmod(remainder, 60)
            full_text = "%ih %im %is remaining" % (hours, minutes, seconds)
            if remaining_time_secs < (15*60):
                urgent = True
                color = "#ff0000"
        else: # Charging, Unknown etc. (My thinkpad says Unknown if close to fully charged)
            energy_full = battery.ENERGY_FULL
            percentage = (energy_now / energy_full) * 100
            full_text = "%.2f%% charged" % percentage

        self.output = {
            "full_text": full_text,
            "name": "pybattery",
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }
