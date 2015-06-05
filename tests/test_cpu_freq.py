#!/usr/bin/env python3

import os
from i3pystatus import cpu_freq


def cpu_freq_test(tfpath, tformat, expected):
    cf = cpu_freq.CpuFreq(file=os.path.join(os.path.dirname(__file__), tfpath), format=tformat)
    cf.run()
    assert cf.output["full_text"] == expected


def test_basic():
    cases = [
        ('cpufreq01', '1240.382', '1236.828', '1203.007', '1264.859', '1236.269'),
    ]
    for path, core0, core1, core2, core3, avg in cases:
        cpu_freq_test(path, "{avg}", avg)
        cpu_freq_test(path, "{core0}", core0)
        cpu_freq_test(path, "{core1}", core1)
        cpu_freq_test(path, "{core2}", core2)
        cpu_freq_test(path, "{core3}", core3)
