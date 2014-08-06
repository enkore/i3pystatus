#!/usr/bin/env python
# -*- coding: utf-8 -*-

from i3pystatus import IntervalModule

class Uptime(IntervalModule):
    """
    Outputs Uptime
    It's possible to include hours, minutes and seconds as: {h},{m} and {s}
    """

    settings = (
        ("format","Format string"),
        ("color","String color"),
        ("alert","If you want the string to change color"),
        ("seconds_alert","How many seconds necessary to start the alert"),
        ("color_alert","Alert color"),
    )

    file           = "/proc/uptime"
    format         = "up {h} hours {m} min"
    color          = "#ffffff"
    alert          = False
    seconds_alert  = 3600
    color_alert    = "#ff0000"

    def run(self):
        with open(self.file,'r') as f:
            data = f.read().split()[0]
            seconds = float(data)
            m, s = divmod(int(seconds), 60)
            h, m = divmod(int(m), 60)

        if self.alert:
            if seconds > self.seconds_alert:
                self.color = self.color_alert
        self.output = {
            "full_text": self.format.format(h=h,m=m,s=s),
            "color": self.color
        }
