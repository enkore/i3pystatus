from i3pystatus import IntervalModule
from subprocess import check_output, CalledProcessError

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
        try:
            out = check_output(self.command, shell=True)
            color = self.color
        except CalledProcessError as e:
            out = e.output
            color = self.error_color

        out = out.decode("UTF-8").replace("\n", " ")

        if out[-1] == " ":
            out = out[:-1]

        self.output = {
            "full_text": out,
            "color": color
        }
