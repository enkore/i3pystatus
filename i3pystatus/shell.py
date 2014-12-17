from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell


class Shell(IntervalModule):
    """
    Shows output of shell command
    """

    color = "#FFFFFF"
    error_color = "#FF0000"

    settings = (
        ("command", "command to be executed"),
        ("color", "standard color"),
        ("error_color", "color to use when non zero exit code is returned")
    )

    required = ("command",)

    def run(self):
        out, success = run_through_shell(self.command, self.enable_log, enable_shell=True)
        self.output = {
            "full_text": out,
            "color": self.color if success else self.error_color
        }
