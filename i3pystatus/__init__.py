from pkgutil import extend_path

from i3pystatus.core import Status
from i3pystatus.core.modules import Module, IntervalModule
from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.util import formatp

import logging
import os

h = logging.FileHandler(".i3pystatus-" + str(os.getpid()), delay=True)

logger = logging.getLogger("i3pystatus")
logger.addHandler(h)
logger.setLevel(logging.CRITICAL)


__path__ = extend_path(__path__, __name__)

__all__ = [
    "Status",
    "Module", "IntervalModule",
    "SettingsBase",
    "formatp",
]


def main():
    from i3pystatus.clock import Clock

    status = Status(standalone=True)
    status.register(Clock())
    status.run()
