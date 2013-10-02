from i3pystatus import IntervalModule
from psutil import virtual_memory

MEGABYTE = 1024**2

class Mem(IntervalModule):
    """
    Shows memory load

    Available formatters:
    * {avail_mem}
    * {percent_used_mem}
    * {used_mem}
    * {total_mem}

    Requires psutil (from PyPI)
    """

    format = "{avail_mem} MB"
    settings = (
        ("format", "format string used for output."),
    )

    def run(self):
        vm = virtual_memory()
        self.output = {
            "full_text" : self.format.format(
                used_mem=int(round(vm.used/MEGABYTE, 0)),
                avail_mem=int(round(vm.available/MEGABYTE, 0)),
                total_mem=int(round(vm.total/MEGABYTE, 0)),
                percent_used_mem=vm.percent)
        }
