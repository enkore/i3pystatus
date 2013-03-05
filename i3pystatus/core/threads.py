import sys
import threading
import time
import traceback

from .util import partition

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        pass

timer = time.perf_counter if hasattr(time, "perf_counter") else time.clock

class Wrapper:
    def __init__(self, workload):
        self.workload = workload

    def __repr__(self):
        return repr(self.workload)

class ExceptionWrapper(Wrapper):
    def __call__(self):
        try:
            self.workload()
        except Exception as exc:
            sys.stderr.write("Exception in {thread}".format(thread=threading.current_thread().name))
            traceback.print_exception(*sys.exc_info(), file=sys.stderr)
            sys.stderr.flush()

class WorkloadWrapper(Wrapper):
    time = 0.0

    def __call__(self):
        tp1 = timer()
        self.workload()
        self.time = timer() - tp1

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

class AutomagicManager:
    def __init__(self, target_interval):
        self.target_interval = target_interval
        self.upper_bound = target_interval * 1.1
        self.lower_bound = target_interval * 0.7

        initial_thread = Thread(target_interval, [self.wrap(self)])
        self.threads = [initial_thread]
        initial_thread.start()

    def __call__(self):
        separate = []
        for thread in self.threads:
            separate.extend(self.branch(thread, thread.time))
        self.create_threads(self.partition(separate))

    def __repr__(self):
        return "Manager"

    def wrap(self, workload):
        return WorkloadWrapper(ExceptionWrapper(workload))

#    def calculate_sparse_times():
#        return ((self.lower_bound - thread.time, thread) for thread in self.threads)

    def branch(self, thread, vtime):
        if len(thread) > 1 and vtime > self.upper_bound:
            remove = thread.pop()
            return [remove] + self.branch(thread, vtime - remove.time)
        return []

    def partition(self, workloads):
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
