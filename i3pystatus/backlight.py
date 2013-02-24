from i3pystatus import IntervalModule

class Backlight(IntervalModule):
    """
    Shows backlight brightness
    """

    settings = (
        ("format", "format string used for output. {brightness}, {max_brightness}, {percentage} are available"),
        ("backlight", "backlight. See /sys/class/backlight/"),
        "color",
    )
    format = "{brightness}/{max_brightness}"
    color = "#FFFFFF"
    backlight = "acpi_video0"

    def init(self):
        self.base_path = "/sys/class/backlight/{backlight}".format(backlight=self.backlight)
  
        with open("{base_path}/max_brightness".format(base_path=self.base_path), "r") as f:
            self.max_brightness = int(f.read())

    def run(self):
        with open("{base_path}/brightness".format(base_path=self.base_path), "r") as f:
            brightness = int(f.read())

        percentage = (brightness / self.max_brightness) * 100
        self.output = {
            "full_text" : self.format.format(brightness=brightness, max_brightness=self.max_brightness, percentage=percentage),
            "color": self.color,
        }
