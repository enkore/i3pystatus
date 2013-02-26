from threading import Thread
import time

from .util import SettingsBase, IntervalWorkerPool

__all__ = [
    "Module", "IntervalModule", "IndependentIntervalModule",
]

class Module(SettingsBase):
    output = None

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            json.insert(0, self.output)

class IndependentIntervalModule(Module):
    interval = 5 # seconds

    def run(self):
        "Called every self.interval seconds"

    def registered(self, status_handler):
        self.thread = Thread(target=self)
        self.thread.daemon = True
        self.thread.start()

    def __call__(self):
        while True:
            self.run()
            time.sleep(self.interval)

class IntervalModule(Module):
    pools = {}
    interval = 5

    def registered(self, status_handler):
        if self.interval in self.pools:
            self.pools[self.interval].items.append(self.run)
        else:
            self.create_pool()

    def create_pool(self):
        pool = IntervalWorkerPool(self.interval)
        pool.items.append(self.run)
        pool.start()
        self.pools[self.interval] = pool
