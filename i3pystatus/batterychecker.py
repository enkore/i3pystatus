#!/usr/bin/env python
# -*- coding: utf-8 -*-

from i3pystatus import IntervalModule

class BatteryChecker(IntervalModule):
    """ 
    This class uses the /proc/acpi/battery interface to check for the
    battery status
    """
    
    def __init__(self, battery_ident="BAT0"):
        self.battery_ident = battery_ident
        self.base_path = "/sys/class/power_supply/%s" % self.battery_ident

    def run(self):
        urgent = False
        color = "#ffffff"
        status = open('%s/status' % self.base_path, 'r').readline().strip()
        energy_now = float(open('%s/energy_now' % self.base_path, 'r').readline())

        if status == 'Full':
            full_text = 'fully charged'
        elif status == 'Charging':
            energy_full = float(open('%s/energy_full' % self.base_path, 'r').readline())
            energy_percentage = (energy_now / energy_full) * 100
            full_text = '%.2f%% charged'
        elif status == 'Discharging':
            power_now = float(open('%s/power_now' % self.base_path, 'r').readline())
            remaining_time_secs = (energy_now / power_now) * 3600
            hours, remainder = divmod(remaining_time_secs, 3600)
            minutes, seconds = divmod(remainder, 60)
            full_text = "%ih %im %is remaining" % (hours, minutes, seconds)
            if remaining_time_secs < (15*60):
                urgent = True
                color = "#ff0000"
        else:
            full_text = 'n/a'

        self.output = {
            "full_text": full_text,
            "name": "pybattery",
            "instance": self.battery_ident,
            "urgent": urgent,
            "color": color
        }
