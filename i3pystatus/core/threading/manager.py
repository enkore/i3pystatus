
from i3pystatus.core.util import partition
from i3pystatus.core.threading import threads, wrapper

class Manager:
    def __init__(self, target_interval):
        self.target_interval = target_interval
        self.upper_bound = target_interval * 1.1
        self.lower_bound = target_interval * 0.7

        initial_thread = threads.Thread(target_interval, [self.wrap(self)])
        self.threads = [initial_thread]

    def __call__(self):
        separate = []
        for thread in self.threads:
            separate.extend(thread.branch(thread.time, self.upper_bound))
        self.create_threads(self.partition_workloads(separate))

    def __repr__(self):
        return "Manager"

    def wrap(self, workload):
        return wrapper.WorkloadWrapper(wrapper.ExceptionWrapper(workload))

    def partition_workloads(self, workloads):
        return partition(workloads, self.lower_bound, lambda workload: workload.time)

    def create_threads(self, threads):
        for workloads in threads: self.create_thread(workloads)

    def create_thread(self, workloads):
        thread = threads.Thread(self.target_interval, workloads, start_barrier=0)
        thread.start()
        self.threads.append(thread)

    def append(self, workload):
        self.threads[0].append(self.wrap(workload))

    def start(self):
        for thread in self.threads: thread.start()
