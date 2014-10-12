import subprocess

from i3pystatus import SettingsBase, IntervalModule


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
        ("action_on_click", "The action to take on left click. Allowed values are 'launch' or 'focus'."
                            "If 'focus' is chosen you must also define the X window class to focus on."
                            "A quick way to find this is to run 'xprop | grep -i class' and click on your mail client."),
        ("window_class", "X window class to focus on click.")
    )
    required = ("backends",)

    color = "#ffffff"
    color_unread = "#ff0000"
    format = "{unread} new email"
    format_plural = "{unread} new emails"
    hide_if_null = True
    email_client = None

    action_on_click = 'launch'
    window_class = None

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
        command = None
        if self.action_on_click == 'launch' and self.email_client:
            command = self.email_client
        elif self.action_on_click == 'focus' and self.window_class:
            command = 'i3-msg -q [class="^%s$"] focus' % self.window_class

        if command:
            subprocess.Popen(command.split())

    def on_rightclick(self):
        self.run()
