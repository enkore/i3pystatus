#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import configparser

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import lchop, TimeWrapper, make_bar
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
        if self.consumption() > 0.1 and self.percentage() < 99.9:
            return "Discharging" if self.battery_info["STATUS"] == "Discharging" else "Charging"
        else:
            return "Full"

    def consumption(self, val):
        return val if val > 0.1 else 0


class BatteryCharge(Battery):
    def __init__(self, bi):
        bi["CHARGE_FULL"] = bi["CHARGE_FULL_DESIGN"] if bi["CHARGE_NOW"] > bi["CHARGE_FULL"] else bi["CHARGE_FULL"]
        super().__init__(bi)

    def consumption(self):
        if "VOLTAGE_NOW" in self.battery_info and "CURRENT_NOW" in self.battery_info:
            return super().consumption(self.battery_info["VOLTAGE_NOW"] * self.battery_info["CURRENT_NOW"])  # V * A = W
        else:
            return -1

    def _percentage(self, design):
        return self.battery_info["CHARGE_NOW"] / self.battery_info["CHARGE_FULL" + design]

    def remaining(self):
        if self.status() == "Discharging":
            if "CHARGE_NOW" in self.battery_info and "CURRENT_NOW" in self.battery_info:
                # Ah / A = h * 60 min = min
                return self.battery_info["CHARGE_NOW"] / self.battery_info["CURRENT_NOW"] * 60
            else:
                return -1
        else:
            return (self.battery_info["CHARGE_FULL"] - self.battery_info["CHARGE_NOW"]) / self.battery_info[
                "CURRENT_NOW"] * 60


class BatteryEnergy(Battery):
    def consumption(self):
        return super().consumption(self.battery_info["POWER_NOW"])

    def _percentage(self, design):
        return self.battery_info["ENERGY_NOW"] / self.battery_info["ENERGY_FULL" + design]

    def remaining(self):
        if self.status() == "Discharging":
            # Wh / W = h * 60 min = min
            return self.battery_info["ENERGY_NOW"] / self.battery_info["POWER_NOW"] * 60
        else:
            return (self.battery_info["ENERGY_FULL"] - self.battery_info["ENERGY_NOW"]) / self.battery_info[
                "POWER_NOW"] * 60


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
    * `{bar}` —bar displaying the percentage graphically
    """

    settings = (
        ("battery_ident", "The name of your battery, usually BAT0 or BAT1"),
        "format",
        ("not_present_text", "Text displayed if the battery is not present. No formatters are available"),
        ("alert", "Display a libnotify-notification on low battery"),
        "alert_percentage",
        ("alert_format_title", "The title of the notification, all formatters can be used"),
        ("alert_format_body", "The body text of the notification, all formatters can be used"),
        ("path", "Override the default-generated path"),
        ("status", "A dictionary mapping ('DIS', 'CHR', 'FULL') to alternative names"),
        ("color", "The text color"),
        ("full_color", "The full color"),
        ("charging_color", "The charging color"),
        ("critical_color", "The critical color"),
        ("not_present_color", "The not present color."),
        ("no_text_full","Don't display text when battery is full - 100%"),
    )
    battery_ident = "BAT0"
    format = "{status} {remaining}"
    status = {
        "CHR": "CHR",
        "DIS": "DIS",
        "FULL": "FULL",
    }
    not_present_text = "Battery not present"

    alert = False
    alert_percentage = 10
    alert_format_title = "Low battery"
    alert_format_body = "Battery {battery_ident} has only {percentage:.2f}% ({remaining:%E%hh:%Mm}) remaining!"
    color = "#ffffff"
    full_color = "#00ff00"
    charging_color = "#00ff00"
    critical_color = "#ff0000"
    not_present_color = "#ffffff"
    no_text_full = False

    path = None

    def init(self):
        if not self.path:
            self.path = "/sys/class/power_supply/{0}/uevent".format(
                self.battery_ident)

    def run(self):
        urgent = False
        color = self.color

        try:
            battery = Battery.create(self.path)
        except FileNotFoundError:
            self.output = {
                "full_text": self.not_present_text,
                "color": self.not_present_color,
            }
            return
        if self.no_text_full:
            if battery.status() == 'Full':
              self.output = {
                  "full_text": ""
              }
              return

        fdict = {
            "battery_ident": self.battery_ident,
            "percentage": battery.percentage(),
            "percentage_design": battery.percentage(design=True),
            "consumption": battery.consumption(),
            "remaining": TimeWrapper(0, "%E%h:%M"),
            "bar": make_bar(battery.percentage()),
        }

        status = battery.status()
        if status in ["Charging", "Discharging"]:
            remaining = battery.remaining()
            fdict["remaining"] = TimeWrapper(remaining * 60, "%E%h:%M")
            if status == "Discharging":
                fdict["status"] = "DIS"
                if battery.percentage() <= self.alert_percentage:
                    urgent = True
                    color = self.critical_color
            else:
                fdict["status"] = "CHR"
                color = self.charging_color
        else:
            fdict["status"] = "FULL"
            color = self.full_color

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
            "full_text": formatp(self.format, **fdict),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color,
        }
