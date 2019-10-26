from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class Yay(Backend):
    """
    This module counts the available updates using yay.
    By default it will only count aur packages. Thus it can be used with the
    pacman backend like this:

    .. code-block:: python

        from i3pystatus.updates import pacman, yay
        status.register("updates", backends = \
[pacman.Pacman(), yay.Yay()])

    To count both pacman and aur packages, pass False in the constructor:

    .. code-block:: python

        from i3pystatus.updates import yay
        status.register("updates", backends = [yay.Yay(False)])
    """

    def __init__(self, aur_only=True):
        self.aur_only = aur_only

    @property
    def updates(self):
        if(self.aur_only):
            command = ["yay", "-Qua"]
        else:
            command = ["yay", "-Qu"]
        checkupdates = run_through_shell(command)
        out = checkupdates.out
        return out.count("\n"), out

Backend = Yay

if __name__ == "__main__":
    """
    Call this module directly; Print the update count and notification body.
    """
    print("Updates: {}\n\n{}".format(*Backend().updates))
