import i3pystatus.backlight as backlight

import os
import pytest

from contextlib import contextmanager
from operator import itemgetter
from tempfile import TemporaryDirectory


@contextmanager
def setattr_temporarily(obj, attr, value):
    old_value = getattr(obj, attr)
    setattr(obj, attr, value)
    yield
    setattr(obj, attr, old_value)


@pytest.mark.parametrize("backlights_data", [
    [],
    [("acpi_video0", 0, 255)],
    [("acpi_video0", 86, 171)],
    [("acpi_video0", 255, 255)],
    [("intel_backlight", 0, 7)],
    [("intel_backlight", 15, 33)],
    [("intel_backlight", 79, 255)],
    [("acpi_video0", 0, 50), ("intel_backlight", 44, 60)],
    [("acpi_video0", 100, 100), ("intel_backlight", 187, 255)],
    [("intel_backlight", 87, 88), ("acpi_video0", 150, 150)],
    [("intel_backlight", 237, 237), ("acpi_video0", 1, 2)],
])
@pytest.mark.parametrize("format", [
    None, "{brightness}/{max_brightness} ({percentage}%)"
])
@pytest.mark.parametrize("format_no_backlight", [
    None, "({percentage}% -- {brightness}) [{max_brightness}]"
])
def test_backlight(backlights_data, format, format_no_backlight):
    print(backlight.Backlight.base_path)
    with TemporaryDirectory() as tmp_dirname:
        for (backlight_name, brightness, max_brightness) in backlights_data:
            backlight_dirname = tmp_dirname + "/" + backlight_name
            os.mkdir(backlight_dirname)

            with open(backlight_dirname + "/brightness", "w") as f:
                print(brightness, file=f)
            with open(backlight_dirname + "/max_brightness", "w") as f:
                print(max_brightness, file=f)

        if not format:
            format = backlight.Backlight.format
        if not format_no_backlight:
            format_no_backlight = backlight.Backlight.format_no_backlight
            if not format_no_backlight:
                format_no_backlight = format

        with setattr_temporarily(backlight.Backlight, 'base_path', tmp_dirname + "/{backlight}/"):
            i3backlight = backlight.Backlight(
                format=format,
                format_no_backlight=format_no_backlight)

        i3backlight.run()

        if len(backlights_data) == 0:
            used_format = format_no_backlight
            cdict = {
                "brightness": -1,
                "max_brightness": -1,
                "percentage": -1
            }
        else:
            backlights_data = sorted(backlights_data, key=itemgetter(0))
            (_, brightness, max_brightness) = backlights_data[0]

            used_format = format
            cdict = {
                "brightness": brightness,
                "max_brightness": max_brightness,
                "percentage": round((brightness / max_brightness) * 100)
            }

        assert i3backlight.output["full_text"] == used_format.format(**cdict)
