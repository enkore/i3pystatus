from i3pystatus import SettingsBase, IntervalModule, formatp


class Backend(SettingsBase):
    """
    TODO: doc
    """

    updates = 0


class Updates(IntervalModule):
    """
    Generic update checker

    TODO: doc
    """

    interval = 60 * 5  # 5 minutes

    settings = (
        ("backends", "List of backends used to check for updates."),
        ("format", ""),
        ("format_no_updates", ""),
        ("color", ""),
        ("color_no_updates", ""),
    )
    required = ("backends",)

    backends = None
    format = "U {count}"
    format_no_updates = None
    color = "#00DD00"
    color_no_updates = "#FFFFFF"

    on_leftclick = "run"

    def init(self):
        if not isinstance(self.backends, list):
            self.backends = [self.backends]
        return

    def run(self):
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
        return
