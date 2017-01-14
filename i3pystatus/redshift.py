import os
import signal
import threading
from subprocess import Popen, PIPE

from i3pystatus import IntervalModule, formatp


class RedshiftController(threading.Thread):

    def __init__(self, args=[]):
        """Initialize controller and start child process

        The parameter args is a list of command line arguments to pass on to
        the child process. The "-v" argument is automatically added."""

        threading.Thread.__init__(self)

        # Initialize state variables
        self._inhibited = False
        self._temperature = 0
        self._period = 'Unknown'
        self._location = (0.0, 0.0)
        self._brightness = 0.0
        self._pid = None

        cmd = ["redshift"] + args
        if "-v" not in cmd:
            cmd += ["-v"]

        env = os.environ.copy()
        env['LANG'] = env['LANGUAGE'] = env['LC_ALL'] = env['LC_MESSAGES'] = 'C'

        self._params = {
            "args": cmd,
            "env": env,
            "bufsize": 1,
            "stdout": PIPE,
            "universal_newlines": True,
        }

    def parse_output(self, line):
        """Convert output to key value pairs"""

        try:
            key, value = line.strip().split(":")
            self.update_value(key, value)
        except ValueError:
            pass

    def update_value(self, key, value):
        """Parse key value pairs to update their values"""

        if key == "Status":
            self._inhibited = value != "Enabled"
        elif key == "Color temperature":
            self._temperature = int(value.rstrip("K"), 10)
        elif key == "Period":
            self._period = value
        elif key == "Brightness":
            self._brightness = value
        elif key == "Location":
            location = []
            for x in value.split(", "):
                v, d = x.split(" ")
                location.append(float(v) * (1 if d in "NE" else -1))
            self._location = (location)

    @property
    def inhibited(self):
        """Current inhibition state"""
        return self._inhibited

    @property
    def temperature(self):
        """Current screen temperature"""
        return self._temperature

    @property
    def period(self):
        """Current period of day"""
        return self._period

    @property
    def location(self):
        """Current location"""
        return self._location

    @property
    def brightness(self):
        """Current brightness"""
        return self._brightness

    def set_inhibit(self, inhibit):
        """Set inhibition state"""
        if self._pid and inhibit != self._inhibited:
            os.kill(self._pid, signal.SIGUSR1)
            self._inhibited = inhibit

    def run(self):
        with Popen(**self._params) as proc:
            self._pid = proc.pid
            for line in proc.stdout:
                self.parse_output(line)
            proc.wait(10)


class Redshift(IntervalModule):
    """
    Show status and control redshift - http://jonls.dk/redshift/.

    This module runs an instance of redshift by itself, since it needs to parse
    its output, so you should remove redshift/redshift-gtk from your i3 config
    before using this module.

    Requires `redshift` installed.

    .. rubric:: Available formatters

    * `{inhibit}` — show if redshift is currently On or Off (using `toggle_inhibit` callback)
    * `{latitude}` — location latitude
    * `{longitude}` — location longitude
    * `{period}` — current period (Day or Night)
    * `{temperature}` — current screen temperature in Kelvin scale (K)

    """
    settings = (
        ("color", "Text color"),
        ("error_color", "Text color when an error occurs"),
        "format",
        ("format_inhibit",
            "List of 2 strings for `{inhibit}`, the first is shown when Redshift is On and the second is shown when Off"),
        ("redshift_parameters", "List of parameters to pass to redshift binary"),
    )

    color = "#ffffff"
    error_color = "#ff0000"
    format = "{inhibit} {temperature}K"
    format_inhibit = ["On", "Off"]
    on_leftclick = "toggle_inhibit"
    redshift_parameters = []

    def init(self):
        self._controller = RedshiftController(self.redshift_parameters)
        self._controller.daemon = True
        self._controller.start()
        self.update_values()

    def update_values(self):
        self.inhibit = self._controller.inhibited
        self.period = self._controller.period
        self.temperature = self._controller.temperature
        self.latitude, self.longitude = self._controller.location
        self.brightness = self._controller.brightness

    def toggle_inhibit(self):
        """Enable/disable redshift"""
        if self.inhibit:
            self._controller.set_inhibit(False)
            self.inhibit = False
        else:
            self._controller.set_inhibit(True)
            self.inhibit = True

    def run(self):
        if self._controller.is_alive():
            self.update_values()
            fdict = {
                "inhibit": self.format_inhibit[int(self.inhibit)],
                "period": self.period,
                "temperature": self.temperature,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "brightness": self.brightness,
            }
            output = formatp(self.format, **fdict)
            color = self.color
        else:
            output = "redshift exited unexpectedly"
            color = self.error_color

        self.output = {
            "full_text": output,
            "color": color,
        }
