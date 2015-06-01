from i3pystatus.core.command import run_through_shell

from i3pystatus.updates import Backend


class Cower(Backend):
    """
    Checks for updates in Arch User Repositories using the `cower` AUR helper.
    """

    @property
    def updates(self):
        command = ["cower", "-u"]
        cower = run_through_shell(command)
        out = cower.out.strip()

        return len(out.split("\n")) if len(out) > 0 else 0

Backend = Cower
