from i3pystatus import IntervalModule
import subprocess


class Xkblayout(IntervalModule):
    """Displays and changes current keyboard layout.

    ``change_layout`` callback finds the current layout in the
    ``layouts`` setting and enables the layout following it. If the
    current layout is not in the ``layouts`` setting the first layout
    is enabled.

    ``layouts`` can be stated with or without variants, e.g.: status.register("xkblayout", layouts=["de neo", "de"])
    """

    interval = 1
    format = u"\u2328 {name}"
    settings = (
        ("layouts", "List of layouts"),
    )
    layouts = []
    on_leftclick = "change_layout"

    def run(self):
        kblayout = subprocess.check_output("setxkbmap -query | awk '/layout/,/variant/{print $2}'", shell=True).decode('utf-8').replace("\n", " ").strip()

        self.output = {
            "full_text": self.format.format(name=kblayout).upper(),
            "color": "#ffffff"
        }

    def change_layout(self):
        layouts = self.layouts
        kblayout = subprocess.check_output("setxkbmap -query | awk '/layout/,/variant/{print $2}'", shell=True).decode('utf-8').replace("\n", " ").strip()
        if kblayout in layouts:
            position = layouts.index(kblayout)
            try:
                subprocess.check_call(["setxkbmap"] + layouts[position + 1].split())
            except IndexError:
                subprocess.check_call(["setxkbmap"] + layouts[0].split())
        else:
            subprocess.check_call(["setxkbmap"] + layouts[0].split())
