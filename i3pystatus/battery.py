import os
import re
import configparser

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import lchop, TimeWrapper, make_bar
from i3pystatus.core.desktop import DesktopNotification
from i3pystatus.core.command import run_through_shell


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
        if self.consumption() is None:
            return self.battery_info["STATUS"]
        elif self.consumption() > 0.1 and self.percentage() < 99.9:
            return "Discharging" if self.battery_info["STATUS"] == "Discharging" else "Charging"
        elif self.consumption() == 0 and self.percentage() == 0.00:
            return "Depleted"
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
            return None

    def _percentage(self, design):
        return self.battery_info["CHARGE_NOW"] / self.battery_info["CHARGE_FULL" + design]

    def wh_remaining(self):
        return self.battery_info['CHARGE_NOW'] * self.battery_info['VOLTAGE_NOW']

    def wh_depleted(self):
        return (self.battery_info['CHARGE_FULL'] - self.battery_info['CHARGE_NOW']) * self.battery_info['VOLTAGE_NOW']

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

    def wh_remaining(self):
        return self.battery_info['ENERGY_NOW']

    def wh_depleted(self):
        return self.battery_info['ENERGY_FULL'] - self.battery_info['ENERGY_NOW']

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
    battery status.

    Setting ``battery_ident`` to ``ALL`` will summarise all available batteries
    and aggregate the % as well as the time remaining on the charge. This is
    helpful when the machine has more than one battery available.

    .. rubric:: Available formatters

    * `{remaining}` — remaining time for charging or discharging, uses TimeWrapper formatting, default format is `%E%h:%M`
    * `{percentage}` — battery percentage relative to the last full value
    * `{percentage_design}` — absolute battery charge percentage
    * `{consumption (Watts)}` — current power flowing into/out of the battery
    * `{status}`
    * `{no_of_batteries}` — The number of batteries included
    * `{battery_ident}` — the same as the setting
    * `{bar}` —bar displaying the relative percentage graphically
    * `{bar_design}` —bar displaying the absolute percentage graphically

    This module supports the :ref:`formatp <formatp>` extended string format
    syntax. By setting the ``FULL`` status to an empty string, and including
    brackets around the ``{status}`` formatter, the text within the brackets
    will be hidden when the battery is full, as can be seen in the below
    example:

    .. code-block:: python

        from i3pystatus import Status

        status = Status()

        status.register(
            'battery',
            interval=5,
            format='{battery_ident}: [{status} ]{percentage_design:.2f}%',
            alert=True,
            alert_percentage=15,
            status = {
                'DPL': 'DPL',
                'CHR': 'CHR',
                'DIS': 'DIS',
                'FULL': '',
            }
        )

        status.run()

    """

    settings = (
        ("battery_ident", "The name of your battery, usually BAT0 or BAT1"),
        "format",
        ("not_present_text", "Text displayed if the battery is not present. No formatters are available"),
        ("alert", "Display a libnotify-notification on low battery"),
        ("critical_level_command", "Runs a shell command in the case of a critical power state"),
        "critical_level_percentage",
        "alert_percentage",
        ("alert_format_title", "The title of the notification, all formatters can be used"),
        ("alert_format_body", "The body text of the notification, all formatters can be used"),
        ("path", "Override the default-generated path and specify the full path for a single battery"),
        ("base_path", "Override the default base path for searching for batteries"),
        ("battery_prefix", "Override the default battery prefix"),
        ("status", "A dictionary mapping ('DPL', 'DIS', 'CHR', 'FULL') to alternative names"),
        ("color", "The text color"),
        ("full_color", "The full color"),
        ("charging_color", "The charging color"),
        ("critical_color", "The critical color"),
        ("not_present_color", "The not present color."),
        ("not_present_text", "The text to display when the battery is not present. Provides {battery_ident} as formatting option"),
        ("no_text_full", "Don't display text when battery is full - 100%"),
    )

    battery_ident = "ALL"
    format = "{status} {remaining}"
    status = {
        "DPL": "DPL",
        "CHR": "CHR",
        "DIS": "DIS",
        "FULL": "FULL",
    }
    not_present_text = "Battery {battery_ident} not present"

    alert = False
    critical_level_command = ""
    critical_level_percentage = 1
    alert_percentage = 10
    alert_format_title = "Low battery"
    alert_format_body = "Battery {battery_ident} has only {percentage:.2f}% ({remaining:%E%hh:%Mm}) remaining!"
    color = "#ffffff"
    full_color = "#00ff00"
    charging_color = "#00ff00"
    critical_color = "#ff0000"
    not_present_color = "#ffffff"
    no_text_full = False

    battery_prefix = 'BAT'
    base_path = '/sys/class/power_supply'
    path = None
    paths = []

    def percentage(self, batteries, design=False):
        total = 0
        for battery in batteries:
            total += battery.percentage(design)
        return total / len(batteries)

    def consumption(self, batteries):
        consumption = 0
        for battery in batteries:
            if battery.consumption() is not None:
                consumption += battery.consumption()
        return consumption

    def abs_consumption(self, batteries):
        abs_consumption = 0
        for battery in batteries:
            if battery.consumption() is None:
                continue
            if battery.status() == 'Discharging':
                abs_consumption -= battery.consumption()
            elif battery.status() == 'Charging':
                abs_consumption += battery.consumption()
        return abs_consumption

    def battery_status(self, batteries):
        abs_consumption = self.abs_consumption(batteries)
        if abs_consumption > 0:
            return 'Charging'
        elif abs_consumption < 0:
            return 'Discharging'
        else:
            return batteries[-1].status()

    def remaining(self, batteries):
        wh_depleted = 0
        wh_remaining = 0
        abs_consumption = self.abs_consumption(batteries)
        for battery in batteries:
            wh_remaining += battery.wh_remaining()
            wh_depleted += battery.wh_depleted()
        if abs_consumption == 0:
            return 0
        elif abs_consumption > 0:
            return wh_depleted / self.consumption(batteries) * 60
        elif abs_consumption < 0:
            return wh_remaining / self.consumption(batteries) * 60

    def init(self):
        if not self.paths or (self.path and self.path not in self.paths):
            bat_dir = self.base_path
            if os.path.exists(bat_dir) and not self.path:
                _, dirs, _ = next(os.walk(bat_dir))
                all_bats = [x for x in dirs if x.startswith(self.battery_prefix)]
                for bat in all_bats:
                    self.paths.append(os.path.join(bat_dir, bat, 'uevent'))
            if self.path:
                self.paths = [self.path]

    def run(self):
        urgent = False
        color = self.color
        batteries = []

        for path in self.paths:
            if self.battery_ident == 'ALL' or path.find(self.battery_ident) >= 0:
                try:
                    batteries.append(Battery.create(path))
                except FileNotFoundError:
                    pass

        if not batteries:
            format_dict = {'battery_ident': self.battery_ident}
            self.output = {
                "full_text": formatp(self.not_present_text, **format_dict),
                "color": self.not_present_color,
            }
            return
        if self.no_text_full:
            if self.battery_status(batteries) == "Full":
                self.output = {
                    "full_text": ""
                }
                return

        fdict = {
            "battery_ident": self.battery_ident,
            "no_of_batteries": len(batteries),
            "percentage": self.percentage(batteries),
            "percentage_design": self.percentage(batteries, design=True),
            "consumption": self.consumption(batteries),
            "remaining": TimeWrapper(0, "%E%h:%M"),
            "bar": make_bar(self.percentage(batteries)),
            "bar_design": make_bar(self.percentage(batteries, design=True)),
        }

        status = self.battery_status(batteries)
        if status in ["Charging", "Discharging"]:
            remaining = self.remaining(batteries)
            fdict["remaining"] = TimeWrapper(remaining * 60, "%E%h:%M")
            if status == "Discharging":
                fdict["status"] = "DIS"
                if self.percentage(batteries) <= self.alert_percentage:
                    urgent = True
                    color = self.critical_color
            else:
                fdict["status"] = "CHR"
                color = self.charging_color
        elif status == 'Depleted':
            fdict["status"] = "DPL"
            color = self.critical_color
        else:
            fdict["status"] = "FULL"
            color = self.full_color
        if self.critical_level_command and fdict["status"] == "DIS" and fdict["percentage"] <= self.critical_level_percentage:
            run_through_shell(self.critical_level_command, enable_shell=True)

        if self.alert and fdict["status"] == "DIS" and fdict["percentage"] <= self.alert_percentage:
            DesktopNotification(
                title=formatp(self.alert_format_title, **fdict),
                body=formatp(self.alert_format_body, **fdict),
                icon="battery-caution",
                urgency=2,
                timeout=60,
            ).display()

        fdict["status"] = self.status[fdict["status"]]

        self.data = fdict
        self.output = {
            "full_text": formatp(self.format, **fdict),
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color,
        }
