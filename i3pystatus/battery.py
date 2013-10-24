#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import configparser

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import lchop, TimeWrapper
from i3pystatus.core.desktop import DesktopNotification


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
        battery_info = UEventParser.parse_file(from_file)
        if "POWER_NOW" in battery_info:
            return BatteryEnergy(battery_info)
        else:
            return BatteryCharge(battery_info)

    def __init__(self, battery_info):
        self.battery_info = battery_info
        self.normalize_micro()

    def normalize_micro(self):
        for key, micro_value in self.battery_info.items():
            if re.match(r"(VOLTAGE|CHARGE|CURRENT|POWER|ENERGY)_(NOW|FULL|MIN)(_DESIGN)?", key):
                self.battery_info[key] = float(micro_value) / 1000000.0

    def percentage(self, design=False):
        return self._percentage("_DESIGN" if design else "") * 100

    def status(self):
        if self.consumption():
            return "Discharging" if self.battery_info["STATUS"] == "Discharging" else "Charging"
        else:
            return "Full"


class BatteryCharge(Battery):
    def consumption(self):
        return self.battery_info["VOLTAGE_NOW"] * self.battery_info["CURRENT_NOW"]  # V  * A = W

    def _percentage(self, design):
        return self.battery_info["CHARGE_NOW"] / self.battery_info["CHARGE_FULL" + design]

    def remaining(self):
        if self.status() == "Discharging":
            # Ah / A = h * 60 min = min
            return self.battery_info["CHARGE_NOW"] / self.battery_info["CURRENT_NOW"] * 60
        else:
            return (self.battery_info["CHARGE_FULL"] - self.battery_info["CHARGE_NOW"]) / self.battery_info["CURRENT_NOW"] * 60


class BatteryEnergy(Battery):
    def consumption(self):
        return self.battery_info["POWER_NOW"]

    def _percentage(self, design):
        return self.battery_info["ENERGY_NOW"] / self.battery_info["ENERGY_FULL" + design]

    def remaining(self):
        if self.status() == "Discharging":
            # Wh / W = h * 60 min = min
            return self.battery_info["ENERGY_NOW"] / self.battery_info["POWER_NOW"] * 60
        else:
            return (self.battery_info["ENERGY_FULL"] - self.battery_info["ENERGY_NOW"]) / self.battery_info["POWER_NOW"] * 60


class BatteryChecker(IntervalModule):
    """
    This class uses the /sys/class/power_supply/…/uevent interface to check for the
    battery status

    Available formatters:

    * `{remaining}` — remaining time for charging or discharging, uses TimeWrapper formatting, default format is `%E%h:%M`
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
        ("alert_format_title",
         "The title of the notification, all formatters can be used"),
        ("alert_format_body",
         "The body text of the notification, all formatters can be used"),
        ("path", "Override the default-generated path"),
        ("status", "A dictionary mapping ('DIS', 'CHR', 'FULL') to alternative names"),
    )
    battery_ident = "BAT0"
    format = "{status} {remaining}"
    status = {
        "CHR": "CHR",
        "DIS": "DIS",
        "FULL": "FULL",
    }

    alert = False
    alert_percentage = 10
    alert_format_title = "Low battery"
    alert_format_body = "Battery {battery_ident} has only {percentage:.2f}% ({remaining:%E%hh:%Mm}) remaining!"

    path = None

    def init(self):
        if not self.path:
            self.path = "/sys/class/power_supply/{0}/uevent".format(
                self.battery_ident)

    def run(self):
        urgent = False
        color = "#ffffff"

        battery = Battery.create(self.path)

        fdict = {
            "battery_ident": self.battery_ident,
            "percentage": battery.percentage(),
            "percentage_design": battery.percentage(design=True),
            "consumption": battery.consumption(),
            "remaining": TimeWrapper(0, "%E%h:%M"),
        }

        status = battery.status()
        if status in ["Discharging", "Charging"]:
            remaining = battery.remaining()
            fdict["remaining"] = TimeWrapper(remaining * 60, "%E%h:%M")
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
            DesktopNotification(
                title=formatp(self.alert_format_title, **fdict),
                body=formatp(self.alert_format_body, **fdict),
                icon="battery-caution",
                urgency=2,
                timeout=60,
            ).display()

        fdict["status"] = self.status[fdict["status"]]

        self.output = {
            "full_text": formatp(self.format, **fdict).strip(),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }
