import subprocess

from i3pystatus import SettingsBase, IntervalModule
from i3pystatus.core.util import internet, require


class Backend(SettingsBase):
    """Handles the details of checking for mail"""

    unread = 0
    """Number of unread mails

    You'll probably implement that as a property"""


class Mail(IntervalModule):
    """
    Generic mail checker

    The `backends` setting determines the backends to use. For available backends see :ref:`mailbackends`
    """

    _endstring = """!!i3pystatus.mail!!"""

    settings = (
        ("backends", "List of backends (instances of ``i3pystatus.mail.xxx.zzz``, i.e. ``i3pystatus.mail.imap.IMAP``)"),
        "color", "color_unread", "format", "format_plural",
        ("hide_if_null", "Don't output anything if there are no new mails"),
        ("email_client", "The email client to open on left click"),
    )
    required = ("backends",)

    color = "#ffffff"
    color_unread = "#ff0000"
    format = "{unread} new email"
    format_plural = "{unread} new emails"
    hide_if_null = True
    email_client = None

    def init(self):
        for backend in self.backends:
            pass

    def run(self):
        unread = sum(map(lambda backend: backend.unread, self.backends))

        if not unread:
            color = self.color
            urgent = "false"
            if self.hide_if_null:
                self.output = None
                return
        else:
            color = self.color_unread
            urgent = "true"

        format = self.format
        if unread > 1:
            format = self.format_plural

        self.output = {
            "full_text": format.format(unread=unread),
            "urgent": urgent,
            "color": color,
        }

    def on_leftclick(self):
        if self.email_client:
            subprocess.Popen(self.email_client.split())

    def on_rightclick(self):
        self.run()
