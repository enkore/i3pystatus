from i3pystatus import IntervalModule
import psutil
import getpass


class MakeWatch(IntervalModule):
    """
    Watches for make jobs and notifies when they are completed.
    requires: psutil
    """

    settings = (
        ("name", "Listen for a job other than 'make' jobs"),
        ("running_color", "Text color while the job is running"),
        ("idle_color", "Text color while the job is not running"),
        "format",
    )
    running_color = "#FF0000"  # red
    idle_color = "#00FF00"   # green
    name = 'make'
    format = "{name}: {status}"

    def run(self):
        status = 'idle'
        for proc in psutil.process_iter():
            cur_proc = proc.as_dict(attrs=['name', 'username'])
            if getpass.getuser() in cur_proc['username']:
                if cur_proc['name'] == self.name:
                    status = proc.as_dict(attrs=['status'])['status']

        if status == 'idle':
            color = self.idle_color
        else:
            color = self.running_color

        cdict = {
            "name": self.name,
            "status": status
        }

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
