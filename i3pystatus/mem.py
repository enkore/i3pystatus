from i3pystatus import IntervalModule
from psutil import virtual_memory

class Mem(IntervalModule):
    """
    Shows memory load
    Available formatters:
    {avail_mem}
    {percent_used_mem}
    {used_mem}
    {total_mem}
    """

    format = "{avail_mem} MB"
    settings = (
        ("format", "format string used for output. {free_mem is the amount of free memory in MB}."),
    )

    def run(self):
        avail_mem = int(round(virtual_memory().available/1024,0))
        used_mem = int(round(virtual_memory().used/1024,0))
        percent_used_mem = int(round(virtual_memory().percent/1024,0))
        total_mem = int(round(virtual_memory().total/1024,0))
        #free_swap = int(round(phymem_usage().free/1024,0))
        self.output = {
            "full_text" : self.format.format(used_mem=used_mem, avail_mem=avail_mem, total_mem=total_mem, percent_used_mem=percent_used_mem)
        }
