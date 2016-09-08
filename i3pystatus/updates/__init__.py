import threading

from i3pystatus import SettingsBase, Module, formatp
from i3pystatus.core.util import internet, require
from i3pystatus.core.desktop import DesktopNotification


class Backend(SettingsBase):
    settings = ()
    updates = 0


class Updates(Module):
    """
    Generic update checker.
    To use select appropriate backend(s) for your system.
    For list of all available backends see :ref:`updatebackends`.

    Left clicking on the module will refresh the count of upgradeable packages.
    This may be used to dismiss the notification after updating your system.

    Right clicking shows a desktop notification with a summary count and a list
    of available updates.

    .. rubric:: Available formatters

    * `{count}` — Sum of all available updates from all backends.
    * For each backend registered there is one formatter named after the
      backend, multiple identical backends do not accumulate, but overwrite
      each other.
    * For example, `{Cower}` (note capital C) is the number of updates
      reported by the cower backend, assuming it has been registered.

    .. rubric:: Usage example

    ::

        from i3pystatus import Status
        from i3pystatus.updates import pacman, cower

        status = Status()

        status.register("updates",
                        format = "Updates: {count}",
                        format_no_updates = "No updates",
                        backends = [pacman.Pacman(), cower.Cower()])

        status.run()

    """

    interval = 3600

    settings = (
        ("backends", "Required list of backends used to check for updates."),
        ("format", "Format used when updates are available. "
         "May contain formatters."),
        ("format_no_updates", "String that is shown if no updates are "
            "available. If not set the module will be hidden if no updates "
            "are available."),
        ("format_working", "Format used while update queries are run. By "
            "default the same as ``format``."),
        ("format_summary", "Format for the summary line of notifications. By "
            "default the same as ``format``."),
        ("notification_icon", "Icon shown when reporting the list of updates. "
            "Default is ``software-update-available``, and can be "
            "None for no icon."),
        "color",
        "color_no_updates",
        "color_working",
        ("interval", "Default interval is set to one hour."),
    )
    required = ("backends",)

    backends = None
    format = "Updates: {count}"
    format_no_updates = None
    format_working = None
    format_summary = None
    notification_icon = "software-update-available"
    color = "#00DD00"
    color_no_updates = None
    color_working = None

    on_leftclick = "run"
    on_rightclick = "report"

    def init(self):
        if not isinstance(self.backends, list):
            self.backends = [self.backends]
        if self.format_working is None:  # we want to allow an empty format
            self.format_working = self.format
        if self.format_summary is None:  # we want to allow an empty format
            self.format_summary = self.format
        self.color_working = self.color_working or self.color
        self.data = {
            "count": 0
        }
        self.notif_body = {}
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.update_thread, daemon=True)
        self.thread.start()

    def update_thread(self):
        self.check_updates()
        while True:
            with self.condition:
                self.condition.wait(self.interval)
            self.check_updates()

    @require(internet)
    def check_updates(self):
        for backend in self.backends:
            key = backend.__class__.__name__
            if key not in self.data:
                self.data[key] = "?"
            if key not in self.notif_body:
                self.notif_body[key] = ""

        self.output = {
            "full_text": formatp(self.format_working, **self.data).strip(),
            "color": self.color_working,
        }

        updates_count = 0
        for backend in self.backends:
            name = backend.__class__.__name__
            updates, notif_body = backend.updates
            updates_count += updates
            self.data[name] = updates
            self.notif_body[name] = notif_body or ""

        if updates_count == 0:
            self.output = {} if not self.format_no_updates else {
                "full_text": self.format_no_updates,
                "color": self.color_no_updates,
            }
            return

        self.data["count"] = updates_count
        self.output = {
            "full_text": formatp(self.format, **self.data).strip(),
            "color": self.color,
        }

    def run(self):
        with self.condition:
            self.condition.notify()

    def report(self):
        DesktopNotification(
            title=formatp(self.format_summary, **self.data).strip(),
            body="\n".join(self.notif_body.values()),
            icon=self.notification_icon,
            urgency=1,
            timeout=0,
        ).display()
