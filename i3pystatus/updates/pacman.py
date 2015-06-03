from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class Pacman(Backend):
    """
    Checks for updates in Arch Linux repositories using the
    `checkupdates` script which is part of the `pacman` package.
    """

    @property
    def updates(self):
        command = ["checkupdates"]
        checkupdates = run_through_shell(command)
        return checkupdates.out.count('\n')

Backend = Pacman
