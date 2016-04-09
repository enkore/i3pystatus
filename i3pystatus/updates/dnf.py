from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend
from re import split


class Dnf(Backend):
    """
    Gets update count for RPM-based distributions with dnf.

    https://dnf.readthedocs.org/en/latest/command_ref.html#check-update-command
    """

    @property
    def updates(self):
        command = ["dnf", "check-update"]
        dnf = run_through_shell(command)

        update_count = 0
        if dnf.rc == 100:
            lines = dnf.out.splitlines()[2:]
            lines = [l for l in lines if len(split("\s{2,}", l.rstrip())) == 3]
            update_count = len(lines)
        return update_count

Backend = Dnf
