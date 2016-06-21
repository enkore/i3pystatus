from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend
from re import split, sub


class Dnf(Backend):
    """
    Gets updates for RPM-based distributions with `dnf check-update`.

    The notification body consists of the status line followed by the package
    name and version for each update.

    https://dnf.readthedocs.org/en/latest/command_ref.html#check-update-command
    """

    @property
    def updates(self):
        command = ["dnf", "check-update"]
        dnf = run_through_shell(command)
        if dnf.err:
            return "?", dnf.err

        raw = dnf.out
        update_count = 0
        if dnf.rc == 100:
            lines = raw.splitlines()[2:]
            lines = [l for l in lines if len(split("\s+", l.rstrip())) == 3]
            update_count = len(lines)
        notif_body = sub(r"(\S+)\s+(\S+)\s+\S+\s*\n", r"\1: \2\n", raw)
        return update_count, notif_body

Backend = Dnf

if __name__ == "__main__":
    """
    Call this module directly; Print the update count and notification body.
    """
    print("Updates: {}\n\n{}".format(*Backend().updates))
