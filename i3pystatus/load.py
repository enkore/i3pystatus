from i3pystatus import IntervalModule
try:
    from os import cpu_count
except ImportError:
    from multiprocessing import cpu_count


class Load(IntervalModule):
    """
    Shows system load

    .. rubric:: Available formatters

    * `{avg1}` — the load average of the last minute
    * `{avg5}` — the load average of the last five minutes
    * `{avg15}` — the load average of the last fifteen minutes
    * `{tasks}` — the number of tasks (e.g. 1/285, which indiciates that one out of 285 total tasks is runnable)
    """

    format = "{avg1} {avg5}"
    settings = (
        "format",
        ("color", "The text color"),
        ("critical_limit", "Limit above which the load is considered critical, defaults to amount of cores."),
        ("critical_color", "The critical color"),
    )

    file = "/proc/loadavg"
    color = "#ffffff"
    critical_limit = cpu_count()
    critical_color = "#ff0000"

    def run(self):
        with open(self.file, "r") as f:
            avg1, avg5, avg15, tasks, lastpid = f.read().split(" ", 5)

        urgent = float(avg1) > self.critical_limit

        self.output = {
            "full_text": self.format.format(avg1=avg1, avg5=avg5, avg15=avg15, tasks=tasks),
            "urgent": urgent,
            "color": self.critical_color if urgent else self.color,
        }
