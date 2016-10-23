import signal
import threading

import gi
gi.require_version('Gtk', '3.0')  # nopep8
from gi.repository import Gtk, GLib
from redshift_gtk.statusicon import RedshiftController

from i3pystatus import IntervalModule, formatp


class Redshift(IntervalModule):
    """
    Show status and control redshift - http://jonls.dk/redshift/.

    This module runs a instace of redshift by itself, since it needs to parse
    its output, so you should remove redshift/redshift-gtk from your i3 config
    before using this module.

    Requires `redshift` and `redshift-gtk`.

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

        self.inhibit = self._controller.inhibited
        self.period = self._controller.period
        self.temperature = self._controller.temperature
        self.latitude, self.longitude = self._controller.location
        self.error = ""

        # Setup signals to property changes
        self._controller.connect('inhibit-changed', self.inhibit_change_cb)
        self._controller.connect('period-changed', self.period_change_cb)
        self._controller.connect('temperature-changed', self.temperature_change_cb)
        self._controller.connect('location-changed', self.location_change_cb)
        self._controller.connect('error-occured', self.error_occured_cb)

        def terminate_child(data=None):
            self._controller.terminate_child()
            return False

        # Install signal handlers
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM,
                             terminate_child, None)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,
                             terminate_child, None)

        try:
            t = threading.Thread(target=Gtk.main)
            t.daemon = True
            t.start()
        except Exception as e:
            self._controller.kill_child()
            self.output = {
                "full_text": "Error creating new thread!",
                "color": self.error_color
            }

    # State update functions
    def inhibit_change_cb(self, controller, inhibit):
        """Callback when controller changes inhibition status"""
        self.inhibit = inhibit

    def period_change_cb(self, controller, period):
        """Callback when controller changes period"""
        self.period = period

    def temperature_change_cb(self, controller, temperature):
        """Callback when controller changes temperature"""
        self.temperature = temperature

    def location_change_cb(self, controller, latitude, longitude):
        """Callback when controlled changes location"""
        self.latitude = latitude
        self.longitude = longitude

    def error_occured_cb(self, controller, error):
        """Callback when an error occurs in the controller"""
        self.error = error

    def toggle_inhibit(self):
        """Enable/disable redshift"""
        if self.inhibit:
            self._controller.set_inhibit(False)
        else:
            self._controller.set_inhibit(True)

    def run(self):
        if self.error:
            fdict = {"error": self.error}
            color = self.error_color
        else:
            fdict = {
                "inhibit": self.format_inhibit[int(self.inhibit)],
                "period": self.period,
                "temperature": self.temperature,
                "latitude": self.latitude,
                "longitude": self.longitude,
            }
            color = self.color

        self.output = {
            "full_text": formatp(self.format, **fdict),
            "color": color,
        }
