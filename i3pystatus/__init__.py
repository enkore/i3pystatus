from pkgutil import extend_path

from i3pystatus.core import Status
from i3pystatus.core.modules import Module, IntervalModule
from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.util import formatp, get_module

import argparse
import imp
import logging
import os

__path__ = extend_path(__path__, __name__)

__all__ = [
    "Status",
    "Module", "IntervalModule",
    "SettingsBase",
    "formatp",
    "get_module",
]

logpath = os.path.join(os.path.expanduser("~"), ".i3pystatus-%s" % os.getpid())
handler = logging.FileHandler(logpath, delay=True)
logger = logging.getLogger("i3pystatus")
logger.addHandler(handler)
logger.setLevel(logging.CRITICAL)


def clock_example():
    from i3pystatus.clock import Clock

    status = Status()
    status.register(Clock())
    status.run()


def main():
    parser = argparse.ArgumentParser(description='''
        run i3pystatus configuration file. Starts i3pystatus clock example if no arguments were provided
    ''')
    parser.add_argument('-c', '--config', help='path to configuration file', default=None, required=False)
    args = parser.parse_args()

    if args.config:
        module_name = "i3pystatus-config"
        imp.load_source(module_name, args.config)
    else:
        clock_example()
