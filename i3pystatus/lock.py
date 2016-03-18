from subprocess import getoutput
from i3pystatus import IntervalModule


class Lock(IntervalModule):
    """
    Locks screen when clicked.
    """

    settings = (
        ("command", "Command to execute upon clicking."),
        "color",
        "format",
    )
    command = "/usr/bin/i3-msg exec /usr/bin/i3lock"
    format = "🔒"
    color = "#ffffff"
    on_leftclick = "lockscreen"

    def run(self):
        self.output = {
            "full_text": self.format,
            "color": self.color
        }

    def lockscreen(self):
        result = getoutput(self.command)
        self.output = {
            "full_text": self.format,
            "color": self.color
        }
