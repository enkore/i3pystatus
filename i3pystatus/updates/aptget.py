import os

from i3pystatus.core.command import run_through_shell
from i3pystatus.updates import Backend


class AptGet(Backend):
    """
    Gets update count for Debian based distributions.

    This mimics the Arch Linux `checkupdates` script
    but with apt-get and written in python.
    """

    @property
    def updates(self):
        cache_dir = "/tmp/update-cache-" + os.getenv("USER")
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

        command = "apt-get update -o Dir::State::Lists=" + cache_dir
        run_through_shell(command.split())
        command = "apt-get upgrade -s -o Dir::State::Lists=" + cache_dir
        apt = run_through_shell(command.split())

        update_count = 0
        for line in apt.out.split("\n"):
            if line.startswith("Inst"):
                update_count += 1
        return update_count

Backend = AptGet
