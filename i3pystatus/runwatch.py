import glob
import os.path

from i3pystatus import IntervalModule


class RunWatch(IntervalModule):
    """
    Expands the given path using glob to a pidfile and checks
    if the process ID found inside is valid
    (that is, if the process is running).
    You can use this to check if a specific application,
    such as a VPN client or your DHCP client is running.

    .. rubric:: Available formatters

    * {pid}
    * {name}
    """

    format_up = "{name}"
    format_down = "{name}"
    color_up = "#00FF00"
    color_down = "#FF0000"
    settings = (
        "format_up", "format_down",
        "color_up", "color_down",
        "path", "name",
    )
    required = ("path", "name")

    @staticmethod
    def is_process_alive(pid):
        return os.path.exists("/proc/{pid}/".format(pid=pid))

    def run(self):
        alive = False
        pid = 0
        try:
            with open(glob.glob(self.path)[0], "r") as f:
                pid = int(f.read().strip())
            alive = self.is_process_alive(pid)
        except Exception:
            pass

        if alive:
            fmt = self.format_up
            color = self.color_up
        else:
            fmt = self.format_down
            color = self.color_down

        self.output = {
            "full_text": fmt.format(name=self.name, pid=pid),
            "color": color,
            "instance": self.name
        }
