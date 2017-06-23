from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell


class Shell(IntervalModule):
    """
    Shows output of shell command

    .. rubric:: Available formatters

    * `{output}` — just the striped command output without newlines
    """

    color = "#FFFFFF"
    error_color = "#FF0000"
    ignore_empty_stdout = False

    settings = (
        ("command", "command to be executed"),
        ("ignore_empty_stdout", "Let the block be empty"),
        ("color", "standard color"),
        ("error_color", "color to use when non zero exit code is returned"),
        "format"
    )

    required = ("command",)
    format = "{output}"

    def run(self):
        retvalue, out, stderr = run_through_shell(self.command, enable_shell=True)

        if retvalue != 0:
            self.logger.error(stderr if stderr else "Unknown error")

        if out:
            out = out.replace("\n", " ").strip()
        elif stderr:
            out = stderr

        full_text = self.format.format(output=out).strip()
        if not full_text and not self.ignore_empty_stdout:
            full_text = "Command `%s` returned %d" % (self.command, retvalue)

        self.output = {
            "full_text": full_text,
            "color": self.color if retvalue == 0 else self.error_color
        }
