import os

from i3pystatus import IntervalModule
import subprocess

class Xkblayout(IntervalModule):
    interval = 1
    format = u"\u2328 {name}"

    def run(self):
        kblayout = subprocess.check_output("setxkbmap -query | awk '/layout/{print $2}'", shell=True)
        layout = kblayout.decode('utf-8').strip().upper()

        self.output = {
            "full_text": self.format.format(name=layout),
            "color": "#ffffff"
        }
