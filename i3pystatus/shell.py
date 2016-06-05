from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell
import logging


class Shell(IntervalModule):
    """
    Shows output of shell command

    .. rubric:: Available formatters

    * `{output}` — just the striped command output without newlines
    """

    color = "#FFFFFF"
    error_color = "#FF0000"

    settings = (
        ("command", "command to be executed"),
        ("color", "standard color"),
        ("error_color", "color to use when non zero exit code is returned"),
        ("hide_if_empty", "Hide output when zero exit code and output is empty"),
        "format"
    )

    hide_if_empty = False

    required = ("command",)
    format = "{output}"

    def run(self):
        retvalue, out, stderr = run_through_shell(self.command, enable_shell=True)

        if retvalue != 0:
            self.logger.error(stderr if stderr else "Unknown error")
        else:
            if self.hide_if_empty and not out:
                self.output = None
                return

        if out:
            out = out.replace("\n", " ").strip()
        elif stderr:
            out = stderr

        self.output = {
            "full_text": self.format.format(output=out) if out else "Command `%s` returned %d" % (self.command, retvalue),
            "color": self.color if retvalue == 0 else self.error_color
        }
