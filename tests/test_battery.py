#!/usr/bin/env python

import os.path

import pytest

from i3pystatus import battery


def battery_test(path, format, expected):
    bc = battery.BatteryChecker(path=os.path.dirname(__file__) + "/" + path, format=format)
    bc.run()
    assert bc.output["full_text"] == expected


@pytest.mark.parametrize("path, status, consumption, remaining, percentage, percentage_design", [
    ("test_battery_basic1", "FULL", "0.000", "0h:00m", "99.91", "76.33"),
    ("test_battery_basic2", "FULL", "0.000", "0h:00m", "100.00", "100.00"),
    ("test_battery_basic3", "DIS", "15.624", "4h:04m", "98.76", "75.45"),
    ("test_battery_basic4", "DIS", "17.510", "1h:46m", "57.43", "57.43"),
    ("test_battery_basic5", "DIS", "11.453", "4h:52m", "97.06", "97.06"),
    ("test_battery_basic6", "CHR", "30.764", "0h:20m", "83.61", "63.88"),
    ("test_battery_basic7", "DIS", "27.303", "1h:44m", "93.99", "91.02"),
    ("test_battery_132", "DIS", "8.370", "1h:17m", "21.95", "21.95"),
    ("test_battery_broken1", "FULL", "0.000", "0h:00m", "100.00", "100.00"),
    ("test_battery_issue89_2", "DIS", "0.000", "0h:00m", "53.51", "51.02"),
    ("test_battery_issue729", "DIS", "4.341", "4h:32m", "66.70", "62.30")
])
def test_basic(path, status, consumption, remaining, percentage, percentage_design):
    battery_test(path, "{status}", status)
    battery_test(path, "{consumption:.3f}", consumption)
    battery_test(path, "{remaining:%hh:%Mm}", remaining)
    battery_test(path, "{percentage:.2f}", percentage)
    battery_test(path, "{percentage_design:.2f}", percentage_design)
