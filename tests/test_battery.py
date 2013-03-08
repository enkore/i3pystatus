#!/usr/bin/env python

import unittest

from i3pystatus import battery

def factory(path, format, expected):
    def test():
        bc = battery.BatteryChecker(path=path, format=format)
        bc.run()
        print(bc.output["full_text"])
        assert bc.output["full_text"] == expected
    test.description = path + ":" + format
    return test

def basic_test_generator():
    cases = [
        ("test_battery_basic1", "FULL", "0.000", ""),
        ("test_battery_basic2", "FULL", "0.000", ""),
        ("test_battery_basic3", "DIS", "15.624", "4h:04m"),
        ("test_battery_basic4", "DIS", "17.510", "1h:46m"),
        ("test_battery_basic5", "DIS", "11.453", "4h:52m"),
        ("test_battery_basic6", "CHR", "30.764", "0h:20m"),
        ("test_battery_basic7", "DIS", "27.303", "1h:44m"),
    ]
    for path, status, consumption, remaining in cases:
        yield factory(path, "{status}", status)
        yield factory(path, "{consumption:.3f}", consumption)
        yield factory(path, "{remaining_hm}", remaining)


#suite = unittest.TestLoader().loadTestsFromName(__name__)
#unittest.TextTestRunner(verbosity=2).run(suite)
