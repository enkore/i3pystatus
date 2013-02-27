
import sys
import threading
import time
import traceback

if hasattr(time, "perf_counter"):
    timer = time.perf_counter
else:
    timer = time.clock

class StderrExcDelegate:
    def __call__(self, exc):
        traceback.print_exception(*sys.exc_info(), file=sys.stderr)

class ExceptionWrapper:
    def __init__(self, workload, exc_delegate):
        self.workload = workload
        self.exc_delegate = exc_delegate

    def __call__(self):
        try:
            self.workload()
        except Exception as exc:
            self.exc_delegate(exc)

    def __repr__(self):
        return repr(self.workload)

class WorkloadWrapper:
    def __init__(self, workload):
        self.workload = workload
        self.time = 0.0

    def __call__(self):
        tp1 = timer()
        self.workload()
        self.time = timer() - tp1

    def __repr__(self):
        return repr(self.workload)

class Thread(threading.Thread):
    def __init__(self, target_interval, workloads=None):
        super().__init__()

        self.workloads = workloads if workloads is not None else []
        self.target_interval = target_interval
        self.daemon = True

    def __iter__(self):
        return iter(self.workloads)

    def __len__(self):
        return len(self.workloads)

    def pop(self):
        return self.workloads.pop()

    def push(self, workload):
        self.workloads.append(workload)

    def run(self):
        while self.workloads:
            for workload in self.workloads:
                workload()

            self.workloads.sort(key=lambda workload: workload.time)

            filltime = self.target_interval - self.time
            if filltime > 0:
                time.sleep(filltime)

    @property
    def time(self):
        return sum(map(lambda workload: workload.time, self.workloads))

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
            separate.extend(self.optimize(thread, thread.time))

        self.create_threads(self.partition(separate))

    def wrap(self, workload):
        return WorkloadWrapper(ExceptionWrapper(workload, exc_delegate=StderrExcDelegate()))

    def optimize(self, thread, vtime):
        if len(thread) > 1 and vtime > self.upper_bound:
            remove = thread.pop()
            return [remove] + self.optimize(thread, vtime - remove.time)
        return []

    def partition(self, workloads):
        timesum = 0.0
        new_threads = []
        current_thread = []
        for workload in workloads:
            current_thread.append(workload)
            timesum += workload.time

            if timesum > self.lower_bound:
                new_threads.append(current_thread)
                current_thread = []
                timesum = 0

        return new_threads

    def create_threads(self, threads):
        for workloads in threads:
            self.create_thread(workloads)

    def create_thread(self, workloads):
        thread = Thread(self.target_interval, workloads)
        thread.start()
        self.threads.append(thread)

    def add(self, workload):
        self.threads[0].push(self.wrap(workload))
