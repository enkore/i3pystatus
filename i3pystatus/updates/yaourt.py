"""
This module counts the available updates using yaourt.
You should not use it together with the pacman backend otherwise
some packeges might be counted twice.
"""

from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend

class Yaourt(Backend):

    @property
    def updates(self):
        command = ["yaourt", "-Qua"]
        checkupdates = run_through_shell(command)
        return checkupdates.out.count('\n')
Backend = Yaourt