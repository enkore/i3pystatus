#!/usr/bin/env python

import sys

from .core import Status
from .core.modules import Module, IntervalModule
from .core.settings import SettingsBase
from .core.config import Config

__all__ = [
    "SettingsBase",
    "Module", "IntervalModule",
    "Status",
]

def main():
    config = Config()
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        config.test()
    else:
        config.run()
