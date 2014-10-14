import subprocess

from i3pystatus import Module


class Text(Module):
    """
    Display static, colored text.
    """

    settings = (
        "text",
        ("color", "HTML color code #RRGGBB"),
        ("cmd_leftclick", "Shell command to execute on left click"),
        ("cmd_rightclick", "Shell command to execute on right click"),
    )
    required = ("text",)

    color = None
    cmd_leftclick = "test"
    cmd_rightclick = "test"

    def init(self):
        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color

    def on_leftclick(self):
        subprocess.call(self.cmd_leftclick, shell=True)

    def on_rightclick(self):
        subprocess.call(self.cmd_rightclick, shell=True)
