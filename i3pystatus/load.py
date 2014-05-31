from i3pystatus import IntervalModule


class Load(IntervalModule):
    """
    Shows system load
    """

    format = "{avg1} {avg5}"
    settings = (
        ("format",
         "format string used for output. {avg1}, {avg5} and {avg15} are the load average of the last one, five and fifteen minutes, respectively. {tasks} is the number of tasks (i.e. 1/285, which indiciates that one out of 285 total tasks is runnable)."),
        ("color", "The text color"),
        ("critical_limit", "Limit above which the load is considered critical"),
        ("critical_color", "The critical color"),
    )

    file = "/proc/loadavg"
    color = "#ffffff"
    critical_limit = 1
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
