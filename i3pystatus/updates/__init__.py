from i3pystatus import SettingsBase, IntervalModule, formatp
from i3pystatus.core.util import internet


class Backend(SettingsBase):
    settings = ()
    updates = 0


class Updates(IntervalModule):
    """
    Generic update checker.
    To use select appropriate backend(s) for your system.
    For list of all available backends see :ref:`updatebackends`.

    Left clicking on the module will refresh the count of upgradeable packages.
    This may be used to dismiss the notification after updating your system.

    .. rubric:: Available formatters

    * `{count}` — Sum of all available updates from all backends.

    .. rubric:: Usage example

    ::

        from i3pystatus import Status
        from i3pystatus.updates import pacman, cower

        status = Status(standalone=True)

        status.register("updates",
                        format = "Updates: {count}",
                        format_no_updates = "No updates",
                        backends = [pacman.Pacman(), cower.Cower()])

        status.run()

    """

    interval = 3600

    settings = (
        ("backends", "Required list of backends used to check for updates."),
        ("format", "String shown when updates are availible. "
         "May contain formatters."),
        ("format_no_updates", "String that is shown if no updates are available."
         " If not set the module will be hidden if no updates are available."),
        "color",
        "color_no_updates",
        ("interval", "Default interval is set to one hour."),
    )
    required = ("backends",)

    backends = None
    format = "Updates: {count}"
    format_no_updates = None
    color = "#00DD00"
    color_no_updates = "#FFFFFF"

    on_leftclick = "run"

    def init(self):
        if not isinstance(self.backends, list):
            self.backends = [self.backends]

    def run(self):
        if not internet():
            self.logger.info("Updates: No internet connection.")
            return

        updates_count = 0
        for backend in self.backends:
            updates_count += backend.updates

        if updates_count == 0:
            self.output = {} if not self.format_no_updates else {
                "full_text": self.format_no_updates,
                "color": self.color_no_updates,
            }
            return

        fdict = {
            "count": updates_count,
        }
        self.output = {
            "full_text": formatp(self.format, **fdict).strip(),
            "color": self.color,
        }
