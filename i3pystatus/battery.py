#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import configparser

from . import IntervalModule
from .core.util import PrefixedKeyDict, lchop
from .core.desktop import display_notification

class UEventParser(configparser.ConfigParser):
    @staticmethod
    def parse_file(file):
        parser = UEventParser()
        with open(file, "r") as file:
            parser.read_string(file.read())
        return dict(parser.items("id10t"))

    def __init__(self):
        super().__init__(default_section="id10t")

    def optionxform(self, key):
        return lchop(key, "POWER_SUPPLY_")

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
            return "Discharging" if self.bat["STATUS"] == "Discharging" else "Charging"
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

    * `{remaining_str}` — remaining time for charging or discharging in the format H:MM
    * `{remaining_hm}`- remaining time in the format Hh:MMm
    * `{percentage}` — battery percentage relative to the last full value
    * `{percentage_design}` — absolute battery charge percentage
    * `{consumption (Watts)}` — current power flowing into/out of the battery
    * `{status}`
    * `{battery_ident}` — the same as the setting
    """

    settings = (
        ("battery_ident", "The name of your battery, usually BAT0 or BAT1"),
        "format",
        ("alert", "Display a libnotify-notification on low battery"),
        "alert_percentage",
        ("alert_format_title", "The title of the notification, all formatters can be used"),
        ("alert_format_body", "The body text of the notification, all formatters can be used"),
        ("path", "Override the default-generated path"),
        ("status", "A dictionary mapping ('DIS', 'CHR', 'FULL') to alternative names"),
    )
    battery_ident = "BAT0"
    format = "{status} {remaining_hm}"
    status = {
        "CHR": "CHR",
        "DIS": "DIS",
        "FULL": "FULL",
    }
    
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

        if self.alert and fdict["status"] == "DIS" and fdict["percentage"] <= self.alert_percentage:
            display_notification(
                title=self.alert_format_title.format(**fdict),
                body=self.alert_format_body.format(**fdict),
                icon="battery-caution",
                urgency=2,
            )

        fdict["status"] = self.status[fdict["status"]]

        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }
