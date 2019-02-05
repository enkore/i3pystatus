from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class Auracle(Backend):
    """
    Checks for updates in Arch User Repositories using the `auracle` AUR helper.

    Depends on auracle AUR agent - https://github.com/falconindy/auracle
    """

    @property
    def updates(self):
        command = ["auracle", "sync"]
        auracle = run_through_shell(command)
        return auracle.out.count('\n'), auracle.out

Backend = Auracle

if __name__ == "__main__":
    """
    Call this module directly; Print the update count and notification body.
    """
    print("Updates: {}\n\n{}".format(*Backend().updates))
