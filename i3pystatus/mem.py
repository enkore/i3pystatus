from i3pystatus import IntervalModule

class Mem(IntervalModule):
    """
    Shows system load
    """

    format = "{free_mem} MB"
    settings = (
        ("format", "format string used for output. {free_mem is the amount of free memory in MB}."),
    )

    file = "/proc/meminfo"

    def run(self):
        with open(self.file, "r") as f:
            free_mem = int(round(int(f.readlines()[1].split()[1])/1024,0))
        self.output = {
            "full_text" : self.format.format(free_mem=free_mem),
        }
