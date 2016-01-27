import subprocess

from i3pystatus import IntervalModule


class Keyboard_locks(IntervalModule):
    """
    Shows the status of CAPS LOCK, NUM LOCK and SCROLL LOCK

    .. rubric:: Available formatters

    * `{caps}` — the current status of CAPS LOCK
    * `{num}` — the current status of NUM LOCK
    * `{scroll}` — the current status of SCROLL LOCK
    """

    interval = 1

    settings = (
        ("format", "Format string"),
        ("caps_on", "String to show in {caps} when CAPS LOCK is on"),
        ("caps_off", "String to show in {caps} when CAPS LOCK is off"),
        ("num_on", "String to show in {num} when NUM LOCK is on"),
        ("num_off", "String to show in {num} when NUM LOCK is off"),
        ("scroll_on", "String to show in {scroll} when SCROLL LOCK is on"),
        ("scroll_off", "String to show in {scroll} when SCROLL LOCK is off"),
        "color"
    )

    format = "{caps} {num} {scroll}"
    caps_on = "CAP"
    caps_off = "___"
    num_on = "NUM"
    num_off = "___"
    scroll_on = "SCR"
    scroll_off = "___"
    color = "#FFFFFF"
    data = {}

    def get_status(self):
        xset = str(subprocess.check_output(["xset", "q"]))
        cap = xset.split("Caps Lock:")[1][0:8]
        num = xset.split("Num Lock:")[1][0:8]
        scr = xset.split("Scroll Lock:")[1][0:8]
        return("on" in cap, "on" in num, "on" in scr)

    def run(self):
        (cap, num, scr) = self.get_status()
        self.data["caps"] = self.caps_on if cap else self.caps_off
        self.data["num"] = self.num_on if num else self.num_off
        self.data["scroll"] = self.scroll_on if scr else self.scroll_off

        output_format = self.format

        self.output = {
            "full_text": output_format.format(**self.data),
            "color": self.color,
        }
