from i3pystatus import IntervalModule
import subprocess

#Example
# status.register("xkblayout",
#    layouts=["es", "us"])


class Xkblayout(IntervalModule):
    interval = 1
    format = u"\u2328 {name}"
    settings = (
        ("layouts", "Layouts list"),
    )
    on_leftclick = "change_layout"

    def run(self):
        kblayout = subprocess.check_output("setxkbmap -query | awk '/layout/{print $2}'", shell=True).decode('utf-8').strip()

        self.output = {
            "full_text": self.format.format(name=kblayout).upper(),
            "color": "#ffffff"
        }
    def change_layout(self):
        layouts=self.layouts
        kblayout = subprocess.check_output("setxkbmap -query | awk '/layout/{print $2}'", shell=True).decode('utf-8').strip()
        if kblayout in layouts:
            position = layouts.index(kblayout)
            try:
                subprocess.check_call(["setxkbmap", layouts[position+1]])
            except IndexError:
                subprocess.check_call(["setxkbmap", layouts[0]])
        else:
            # Go to first position
            subprocess.check_call(["setxkbmap", layouts[0]])
