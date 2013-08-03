#!/usr/bin/env python

import sys
import argparse

from i3pystatus.core import Status
from i3pystatus.core.modules import Module, IntervalModule
from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.config import Config
from i3pystatus.core.util import formatp

__all__ = [
    "SettingsBase",
    "Module", "IntervalModule",
    "Status",
    "formatp",
]

def main():
    parser = argparse.ArgumentParser(description="A replacement for i3status")
    parser.add_argument("-c", "--config", action="store", help="Config file")
    parser.add_argument("-t", "--test", action="store_true", help="Test modules")
    args = parser.parse_args()

    config = Config(config_file=args.config)
    if args.test:
        config.test()
    else:
        config.run()
