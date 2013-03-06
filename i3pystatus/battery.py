#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import IntervalModule
from .core.util import PrefixedKeyDict
from .core.desktop import display_notification

class Battery:
    @staticmethod
    def lchop(string, prefix="POWER_SUPPLY_"):
        if string.startswith(prefix):
            return string[len(prefix):]
        return string

    @staticmethod
    def map_key(key):
        return Battery.lchop(key).replace("CHARGE", "ENERGY")

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

        setattr(self, self.map_key(key), self.convert(value))

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

    Available formatters for format and alert_format_\*:

    * remaining_str
    * remaining_hm
    * percentage
    * percentage_design
    * consumption (Watts)
    * status
    * battery_ident
    """
    
    settings = (
        "battery_ident", "format",
        ("alert", "Display a libnotify-notification on low battery"),
        "alert_percentage", "alert_format_title", "alert_format_body", "alert_percentage",
    )
    battery_ident = "BAT0"
    format = "{status} {remaining_hm}"
    
    alert = False
    alert_percentage = 10
    alert_format_title = "Low battery"
    alert_format_body = "Battery {battery_ident} has only {percentage:.2f}% ({remaining_hm}) remaining!"

    def init(self):
        self.base_path = "/sys/class/power_supply/{0}/uevent".format(self.battery_ident)

    def run(self):
        urgent = False
        color = "#ffffff"

        battery = Battery(self.base_path)

        status = battery.STATUS
        energy_now = battery.ENERGY_NOW
        energy_full = battery.ENERGY_FULL
        if not hasattr(battery, "POWER_NOW"):
            battery.POWER_NOW = battery.VOLTAGE_NOW * battery.CURRENT_NOW
        power_now = battery.POWER_NOW

        fdict = {
            "battery_ident": self.battery_ident,
            "remaining_str": "",
            "remaining_hm": "",
            "percentage": (energy_now / energy_full) * 100,
            "percentage_design": (energy_now / battery.ENERGY_FULL_DESIGN) * 100,
            "consumption": power_now / 1000000,
        }

        if status == "Full" or fdict["percentage"] > 99:
            fdict["status"] = "FULL"
        elif power_now:
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

        if self.alert and fdict["percentage"] <= self.alert_percentage:
            display_notification(
                title=self.alert_format_title.format(**fdict),
                body=self.alert_format_body.format(**fdict),
                icon="battery-caution",
                urgency=2,
            )

        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }
