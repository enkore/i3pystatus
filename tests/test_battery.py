#!/usr/bin/env python

import os.path

import pytest

from i3pystatus import battery


def battery_test(path, format, expected):
    bc = battery.BatteryChecker(path=os.path.dirname(__file__) + "/" + path, format=format)
    bc.run()
    assert bc.output["full_text"] == expected


@pytest.mark.parametrize("path, status, consumption, remaining", [
    ("test_battery_basic1", "FULL", "0.000", "0h:00m"),
    ("test_battery_basic2", "FULL", "0.000", "0h:00m"),
    ("test_battery_basic3", "DIS", "15.624", "4h:04m"),
    ("test_battery_basic4", "DIS", "17.510", "1h:46m"),
    ("test_battery_basic5", "DIS", "11.453", "4h:52m"),
    ("test_battery_basic6", "CHR", "30.764", "0h:20m"),
    ("test_battery_basic7", "DIS", "27.303", "1h:44m"),
    ("test_battery_132", "DIS", "8.370", "1h:17m"),
    ("test_battery_broken1", "FULL", "0.000", "0h:00m"),
    ("test_battery_issue89_2", "DIS", "0.000", "0h:00m"),
])
def test_basic(path, status, consumption, remaining):
    battery_test(path, "{status}", status)
    battery_test(path, "{consumption:.3f}", consumption)
    battery_test(path, "{remaining:%hh:%Mm}", remaining)
