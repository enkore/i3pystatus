#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import configparser

from . import IntervalModule
from .core.util import PrefixedKeyDict
from .core.desktop import display_notification

class UEventParser(configparser.ConfigParser):
    @staticmethod
    def parse_file(file):
        parser = UEventParser()
        with open(file, "r") as file:
            parser.read_string(file.read())
        return dict(parser.items("id10t"))

    @staticmethod
    def lchop(string, prefix):
        if string.startswith(prefix):
            return string[len(prefix):]
        return string

    def __init__(self):
        super().__init__(default_section="id10t")

    def optionxform(self, key):
        return self.lchop(key, "POWER_SUPPLY_")

    def read_string(self, string):
        super().read_string("[id10t]\n" + string)

class Battery:
    @staticmethod
    def create(from_file):
        batinfo = UEventParser.parse_file(from_file)
        if "POWER_NOW" in batinfo:
            return BatteryEnergy(batinfo)
        else:
            return BatteryCharge(batinfo)

    def __init__(self, batinfo):
        self.bat = batinfo
        self.normalize_µ()

    def normalize_µ(self):
        for key, µvalue in self.bat.items():
            if re.match(r"(VOLTAGE|CHARGE|CURRENT|POWER|ENERGY)_(NOW|FULL|MIN)(_DESIGN)?", key):
                self.bat[key] = float(µvalue) / 1000000.0

    def percentage(self, design=False):
        return self._percentage("_DESIGN" if design else "") * 100

    def status(self):
        if self.consumption():
            if self.bat["STATUS"] == "Discharging":
                return "Discharging"
            else:
                return "Charging"
        else:
            return "Full"

class BatteryCharge(Battery):
    def consumption(self):
        return self.bat["VOLTAGE_NOW"] * self.bat["CURRENT_NOW"] # V  * A = W

    def _percentage(self, design):
        return self.bat["CHARGE_NOW"] / self.bat["CHARGE_FULL"+design]

    def remaining(self):
        if self.status() == "Discharging":
            return self.bat["CHARGE_NOW"] / self.bat["CURRENT_NOW"] * 60 # Ah / A = h * 60 min = min
        else:
            return (self.bat["CHARGE_FULL"] - self.bat["CHARGE_NOW"]) / self.bat["CURRENT_NOW"] * 60

class BatteryEnergy(Battery):
    def consumption(self):
        return self.bat["POWER_NOW"]

    def _percentage(self, design):
        return self.bat["ENERGY_NOW"] / self.bat["ENERGY_FULL"+design]

    def remaining(self):
        if self.status() == "Discharging":
            return self.bat["ENERGY_NOW"] / self.bat["POWER_NOW"] * 60 # Wh / W = h * 60 min = min
        else:
            return (self.bat["ENERGY_FULL"] - self.bat["ENERGY_NOW"]) / self.bat["POWER_NOW"] * 60

def format_remaining(minutes, prefix):
    hours, minutes = map(int, divmod(minutes, 60))

    d = PrefixedKeyDict(prefix)
    d.update({
        "str": "{}:{:02}".format(hours, minutes),
        "hm": "{}h:{:02}m".format(hours, minutes),
        "hours": hours,
        "mins": minutes,
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
    interval=1
    settings = (
        "battery_ident", "format",
        ("alert", "Display a libnotify-notification on low battery"),
        "alert_percentage", "alert_format_title", "alert_format_body", "alert_percentage",
        "path",
    )
    battery_ident = "BAT0"
    format = "{status} {remaining_hm}"
    
    alert = False
    alert_percentage = 10
    alert_format_title = "Low battery"
    alert_format_body = "Battery {battery_ident} has only {percentage:.2f}% ({remaining_hm}) remaining!"

    path = None

    def init(self):
        if not self.path:
            self.path = "/sys/class/power_supply/{0}/uevent".format(self.battery_ident)

    def run(self):
        urgent = False
        color = "#ffffff"

        battery = Battery.create(self.path)

        fdict = {
            "battery_ident": self.battery_ident,
            "remaining_str": "",
            "remaining_hm": "",
            "percentage": battery.percentage(),
            "percentage_design": battery.percentage(design=True),
            "consumption": battery.consumption(),
        }

        status = battery.status()
        if status in ["Discharging", "Charging"]:
            remaining = battery.remaining()
            fdict.update(format_remaining(remaining, "remaining_"))
            if status == "Discharging":
                fdict["status"] = "DIS"
                if remaining < 15:
                    urgent = True
                    color = "#ff0000"
            else:
                fdict["status"] = "CHR"
        else:
            fdict["status"] = "FULL"

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
