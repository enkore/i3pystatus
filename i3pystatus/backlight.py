from i3pystatus.file import File
from i3pystatus import Module
from i3pystatus.core.command import run_through_shell
import glob
import shutil


class Backlight(File):
    """
    Screen backlight info

    - (Optional) requires `xbacklight` to change the backlight brightness with the scollwheel.

    .. rubric:: Available formatters

    * `{brightness}` — current brightness relative to max_brightness
    * `{max_brightness}` — maximum brightness value
    * `{percentage}` — current brightness in percent
    """

    settings = (
        ("format", "format string, formatters: brightness, max_brightness, percentage"),
        ("format_no_backlight", "format string when no backlight file available"),
        ("backlight",
            "backlight, see `/sys/class/backlight/`. Supports glob expansion, i.e. `*` matches anything. "
            "If it matches more than one filename, selects the first one in alphabetical order"),
        "color",
    )
    required = ()

    backlight = "*"
    format = "{brightness}/{max_brightness}"
    format_no_backlight = "No backlight"

    base_path = "/sys/class/backlight/{backlight}/"
    components = {
        "brightness": (int, "brightness"),
        "max_brightness": (int, "max_brightness"),
    }
    transforms = {
        "percentage": lambda cdict: round((cdict["brightness"] / cdict["max_brightness"]) * 100),
    }
    on_upscroll = "lighter"
    on_downscroll = "darker"

    def init(self):
        self.has_xbacklight = shutil.which("xbacklight") is not None

        self.base_path = self.base_path.format(backlight=self.backlight)
        backlight_entries = sorted(glob.glob(self.base_path))

        if len(backlight_entries) == 0:
            self.run = self.run_no_backlight
            super().init()
            return

        self.base_path = backlight_entries[0]

        # xbacklight expects a percentage as parameter. Calculate the percentage
        # for one step (if smaller xbacklight doesn't increases the brightness)
        if self.has_xbacklight:
            parsefunc = self.components['max_brightness'][0]
            maxbfile = self.components['max_brightness'][1]
            with open(self.base_path + maxbfile, "r") as f:
                max_steps = parsefunc(f.read().strip())
                if max_steps:
                    self.step_size = 100 // max_steps + 1
                else:
                    self.step_size = 5  # default?
        super().init()

    def run_no_backlight(self):
        cdict = {
            "brightness": -1,
            "max_brightness": -1,
            "percentage": -1
        }

        self.data = cdict
        self.output = {
            "full_text": self.format_no_backlight.format(**cdict),
            "color": self.color
        }

    def lighter(self):
        if self.has_xbacklight:
            run_through_shell(["xbacklight", "-inc", str(self.step_size)])

    def darker(self):
        if self.has_xbacklight:
            run_through_shell(["xbacklight", "-dec", str(self.step_size)])
