import threading
import time
import sys
from i3pystatus.core.util import partition

timer = time.perf_counter if hasattr(time, "perf_counter") else time.clock


def unwrap_workload(workload):
    """ Obtain the module from it's wrapper. """
    while isinstance(workload, Wrapper):
        workload = workload.workload
    return workload


class Thread(threading.Thread):
    def __init__(self, target_interval, workloads=None, start_barrier=1):
        super().__init__()
        self.workloads = workloads or []
        self.target_interval = target_interval
        self.start_barrier = start_barrier
        self._suspended = threading.Event()
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
            if self.should_execute(workload):
                workload()
        self.workloads.sort(key=lambda workload: workload.time)

    def should_execute(self, workload):
        """
        If we have been suspended by i3bar, only execute those modules that set the keep_alive flag to a truthy
        value. See the docs on the suspend_signal_handler method of the io module for more information.
        """
        if not self._suspended.is_set():
            return True
        workload = unwrap_workload(workload)
        return hasattr(workload, 'keep_alive') and getattr(workload, 'keep_alive')

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

    def suspend(self):
        self._suspended.set()

    def resume(self):
        self._suspended.clear()


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
            message = "Exception in {thread} at {time}, module {name}".format(
                thread=threading.current_thread().name,
                time=time.strftime("%c"),
                name=self.workload.__class__.__name__
            )
            if hasattr(self.workload, "logger"):
                self.workload.logger.error(message, exc_info=True)
            self.workload.output = {
                "full_text": self.format_exception(),
                "color": "#FF0000",
            }

    def format_exception(self):
        type, value, _ = sys.exc_info()
        exception = self.truncate_error("%s: %s" % (type.__name__, value))
        return "%s: %s" % (self.workload.__class__.__name__, exception)

    def truncate_error(self, exception_message):
        if hasattr(self.workload, 'max_error_len'):
            error_len = self.workload.max_error_len
            if len(exception_message) > error_len:
                return exception_message[:error_len] + '…'
            else:
                return exception_message
        else:
            return exception_message


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

    def suspend(self):
        for thread in self.threads:
            thread.suspend()

    def resume(self):
        for thread in self.threads:
            thread.resume()
