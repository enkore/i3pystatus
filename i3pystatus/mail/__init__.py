
from i3pystatus import SettingsBase, IntervalModule

class Backend(SettingsBase):
    """Handles the details of checking for mail"""

    unread = 0
    """Number of unread mails

    You'll probably implement that as a property"""

class Mail(IntervalModule):
    """
    Generic mail checker

    The `backends` setting determines the backends to use. Currently available are:
    """

    _endstring = """
    Currently available backends are:

!!i3pystatus.mail!!"""

    settings = (
        ("backends", "List of backends (instances of i3pystatus.mail.xxx)"),
        "color", "color_unread", "format", "format_plural"
    )
    required = ("backends",)

    color = "#ffffff"
    color_unread  ="#ff0000"
    format = "{unread} new email"
    format_plural = "{unread} new emails"

    def init(self):
        for backend in self.backends:
            pass

    def run(self):
        unread = sum(map(lambda backend: backend.unread, self.backends))

        if not unread:
            color = self.color
            urgent = "false"
        else:
            color = self.color_unread
            urgent = "true"

        format = self.format
        if unread > 1:
            format = self.format_plural

        self.output = {
            "full_text" : format.format(unread=unread),
            "urgent" : urgent,
            "color" : color,
        }
