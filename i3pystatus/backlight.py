from i3pystatus.file import File
from i3pystatus import Module
import shutil
import subprocess


class Backlight(File):
    """
    Screen backlight info

    .. rubric:: Available formatters

    * `{brightness}` — current brightness relative to max_brightness
    * `{max_brightness}` — maximum brightness value
    * `{percentage}` — current brightness in percent
    """

    settings = (
        ("format", "format string, formatters: brightness, max_brightness, percentage"),
        ("backlight", "backlight, see `/sys/class/backlight/`"),
        "color",
    )
    required = ()

    backlight = "acpi_video0"
    format = "{brightness}/{max_brightness}"

    base_path = "/sys/class/backlight/{backlight}/"
    components = {
        "brightness": (int, "brightness"),
        "max_brightness": (int, "max_brightness"),
    }
    transforms = {
        "percentage": lambda cdict: (cdict["brightness"] / cdict["max_brightness"]) * 100,
    }
    on_upscroll = "lighter"
    on_downscroll = "darker"
    def init(self):
        self.base_path = self.base_path.format(backlight=self.backlight)
        self.has_xbacklight = shutil.which("xbacklight") is not None
        super(Backlight, self).init()

    def lighter(self):
        if self.has_xbacklight:
            subprocess.Popen(["xbacklight", '+5'])

    def darker(self):
        if self.has_xbacklight:
            subprocess.Popen(["xbacklight", '-5'])
