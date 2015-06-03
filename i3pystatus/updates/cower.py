from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class Cower(Backend):
    """
    Checks for updates in Arch User Repositories using the `cower` AUR helper.

    Depends on cower AUR agent - https://github.com/falconindy/cower
    """

    @property
    def updates(self):
        command = ["cower", "-u"]
        cower = run_through_shell(command)
        return cower.out.count('\n')

Backend = Cower
