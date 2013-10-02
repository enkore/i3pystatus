from i3pystatus import IntervalModule
from psutil import virtual_memory

class Mem(IntervalModule):
    """
    Shows memory load

    Available formatters:
    * {avail_mem}
    * {percent_used_mem}
    * {used_mem}
    * {total_mem}
    """

    format = "{avail_mem} MB"
    settings = (
        ("format", "format string used for output."),
    )

    def run(self):
        vm = virtual_memory()
        avail_mem = int(round(vm.available/1024, 0))
        used_mem = int(round(vm.used/1024, 0))
        percent_used_mem = int(round(vm.percent/1024, 0))
        total_mem = int(round(vm.total/1024, 0))
        #free_swap = int(round(phymem_usage().free/1024,0))
        self.output = {
            "full_text" : self.format.format(
                used_mem=used_mem,
                avail_mem=avail_mem,
                total_mem=total_mem,
                percent_used_mem=percent_used_mem)
        }
