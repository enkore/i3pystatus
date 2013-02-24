from os.path import join

from i3pystatus import IntervalModule

class File(IntervalModule):
    """
    Rip information from text files

    components is a dict of pairs of the form:

        name => (callable, file)

    * Where `name` is a valid identifier, which is used in the format string to access
    the value of that component.
    * `callable` is some callable to convert the contents of `file`. A common choice is
    float or int.
    * `file` names a file, relative to `base_path`.

    transform is a optional dict of callables taking a single argument, a dictionary containing the values
    of all components. The return value is bound to `name`
    """

    settings = (
        ("format", "format string"),
        ("components", "List of tripels"),
        ("transforms", "List of pairs"),
        ("base_path", ""),
        "color", "interval",
    )
    required = ("format", "components")
    base_path = "/"
    transforms = tuple()
    color = "#FFFFFF"

    def run(self):
        cdict = {}

        for key, (component, file) in self.components.items():
            with open(join(self.base_path, file), "r") as f:
                cdict[key] = component(f.read().strip())

        for key, transform in self.transforms.items():
            cdict[key] = transform(cdict)

        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.color
        }

def backlight(backlight="acpi_video0", format="{brightness}/{max_brightness}"):
    """
    Backlight info template

    Available formatters:
    * brightness
    * max_brightness
    * percentage
    """

    return File(
        base_path="/sys/class/backlight/{backlight}/".format(backlight=backlight),
        components={
            "brightness": (int, "brightness"),
            "max_brightness": (int, "max_brightness"),
        },
        transforms={
            "percentage": lambda cdict: (cdict["brightness"] / cdict["max_brightness"]) * 100,
        },
        format="{brightness}/{max_brightness}",
        interval=1
    )
