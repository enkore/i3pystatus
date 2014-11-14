import threading
import time
import sys
import traceback
from i3pystatus.core.util import partition

timer = time.perf_counter if hasattr(time, "perf_counter") else time.clock


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

    def execute_workloads(self):
        for workload in self:
            workload()
        self.workloads.sort(key=lambda workload: workload.time)

    def run(self):
        while self:
            self.execute_workloads()
            filltime = self.target_interval - self.time
            if filltime > 0:
                time.sleep(filltime)

    def branch(self, vtime, bound):
        if len(self) > 1 and vtime > bound:
            remove = self.pop()
            return [remove] + self.branch(vtime - remove.time, bound)
        return []


class Wrapper:
    def __init__(self, workload):
        self.workload = workload

    def __repr__(self):
        return repr(self.workload)


class ExceptionWrapper(Wrapper):
    def __call__(self):
        try:
            self.workload()
        except:
            sys.stderr.write("Exception in {thread} at {time}\n".format(
                thread=threading.current_thread().name,
                time=time.strftime("%c")
            ))
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            if hasattr(self.workload, "output"):
                self.workload.output = {
                    "full_text": "{}: {}".format(self.workload.__class__.__name__, sys.exc_info()[1]),
                    "color": "#FF0000",
                }


class WorkloadWrapper(Wrapper):
    time = 0.0

    def __call__(self):
        tp1 = timer()
        self.workload()
        self.time = timer() - tp1


class Manager:
    def __init__(self, target_interval):
        self.target_interval = target_interval
        self.upper_bound = target_interval * 1.1
        self.lower_bound = target_interval * 0.7

        initial_thread = Thread(target_interval, [self.wrap(self)])
        self.threads = [initial_thread]

    def __call__(self):
        separate = []
        for thread in self.threads:
            separate.extend(thread.branch(thread.time, self.upper_bound))
        self.create_threads(self.partition_workloads(separate))

    def __repr__(self):
        return "Manager"

    def wrap(self, workload):
        return WorkloadWrapper(ExceptionWrapper(workload))

    def partition_workloads(self, workloads):
        return partition(workloads, self.lower_bound, lambda workload: workload.time)

    def create_threads(self, threads):
        for workloads in threads:
            self.create_thread(workloads)

    def create_thread(self, workloads):
        thread = Thread(self.target_interval, workloads, start_barrier=0)
        thread.start()
        self.threads.append(thread)

    def append(self, workload):
        self.threads[0].append(self.wrap(workload))

    def start(self):
        for thread in self.threads:
            thread.start()
