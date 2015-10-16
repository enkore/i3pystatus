import re
from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class Yaourt(Backend):
    """
    This module counts the available updates using yaourt.
    By default it will only count aur packages. Thus it can be used with the pacman backend like this:

    from i3pystatus.updates import pacman, yaourt
    status.register("updates", backends = [pacman.Pacman(), yaourt.Yaourt()])

    If you want to count both pacman and aur packages with this module you can set the variable
    count_only_aur = False like this:

    from i3pystatus.updates import yaourt
    status.register("updates", backends = [yaourt.Yaourt(False)])
    """

    def __init__(self, aur_only=True):
        self.aur_only = aur_only

    @property
    def updates(self):
        command = ["yaourt", "-Qua"]
        checkupdates = run_through_shell(command)
        if(self.aur_only):
            return len(re.findall("^aur/", checkupdates.out, flags=re.M))
        return checkupdates.out.count("\n")

Backend = Yaourt
