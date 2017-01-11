import os

from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class PackageKit(Backend):
    """
    Gets update count for distributions using PackageKit.

    At the moment, it works with english localization, only.
    """

    @property
    def updates(self):
        command = "pkcon get-updates -p"
        pk = run_through_shell(command.split())

        out = pk.out.splitlines(True)
        resultStrings = ("Security", "Bug fix", "Enhancement")
        out = "".join([line for line in out[out.index("Results:\n") + 1:]
                       if line.startswith(resultStrings)])
        return out.count("\n"), out

Backend = PackageKit

if __name__ == "__main__":
    """
    Call this module directly; Print the update count and notification body.
    """
    print("Updates: {}\n\n{}".format(*Backend().updates))
