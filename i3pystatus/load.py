from i3pystatus import IntervalModule


class Load(IntervalModule):

    """
    Shows system load
    """

    format = "{avg1} {avg5}"
    settings = (
        ("format",
         "format string used for output. {avg1}, {avg5} and {avg15} are the load average of the last one, five and fifteen minutes, respectively. {tasks} is the number of tasks (i.e. 1/285, which indiciates that one out of 285 total tasks is runnable)."),
        ("critical_limit", "Limit under witch one the battery is critical"),
        ("critical_color", "The critical color"),
    )

    file = "/proc/loadavg"

    def run(self):
        with open(self.file, "r") as f:
            avg1, avg5, avg15, tasks, lastpid = f.read().split(" ", 5)

        self.output = {
            "full_text": self.format.format(avg1=avg1, avg5=avg5, avg15=avg15, tasks=tasks),
        }
