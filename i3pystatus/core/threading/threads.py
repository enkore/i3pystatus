
import time
import threading

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        pass

class Thread(threading.Thread):
    def __init__(self, target_interval, workloads=None, start_barrier=1):
        super().__init__()
        self.workloads = workloads or []
        self.target_interval = target_interval
        self.start_barrier = start_barrier
        self.daemon = True

    def __iter__(self):
        return iter(self.workloads)

    def __len__(self):
        return len(self.workloads)

    def pop(self):
        return self.workloads.pop()

    def append(self, workload):
        self.workloads.append(workload)

    @property
    def time(self):
        return sum(map(lambda workload: workload.time, self))

    def wait_for_start_barrier(self):
        while len(self) <= self.start_barrier:
            time.sleep(0.4)

    def setproctitle(self):
        setproctitle("i3pystatus {name}: {workloads}".format(name=self.name, workloads=list(map(repr, self.workloads))))

    def execute_workloads(self):
        for workload in self:
            workload()
        self.workloads.sort(key=lambda workload: workload.time)

    def run(self):
        self.setproctitle()
        while self:
            self.execute_workloads()
            filltime = self.target_interval - self.time
            if filltime > 0:
                time.sleep(filltime)
