from i3pystatus import SettingsBase, IntervalModule
from i3pystatus.core.command import run_through_shell


class Backend(SettingsBase):
    """Handles the details of checking for mail"""

    unread = 0
    settings = (("account", "Account name"),)

    account = "Default account"

    """Number of unread mails

    You'll probably implement that as a property"""


class Mail(IntervalModule):
    """
    Generic mail checker

    The `backends` setting determines the backends to use. For available backends see :ref:`mailbackends`.
    """

    settings = (
        ("backends", "List of backends (instances of ``i3pystatus.mail.xxx.zzz``, e.g. :py:class:`.imap.IMAP`)"),
        "color", "color_unread", "format", "format_plural",
        ("hide_if_null", "Don't output anything if there are no new mails"),
        ("email_client", "The command to run on left click. "
                         "For example, to launch Thunderbird set ``email_client` to ``thunderbird``. "
                         "Alternatively, to bring Thunderbird into focus, "
                         "set ``email_client`` to ``i3-msg -q [class=\"^Thunderbird$\"] focus``. "
                         "Hint: To discover the X window class of your email client run 'xprop | grep -i class' "
                         "and click on it's window\n"),
    )
    required = ("backends",)

    color = "#ffffff"
    color_unread = "#ff0000"
    format = "{unread} new email"
    format_plural = "{account} : {current_unread}/{unread} new emails"
    hide_if_null = True
    email_client = None

    on_leftclick = "open_client"
    on_upscroll = ["scroll_backend", 1]
    on_downscroll = ["scroll_backend", -1]

    current_backend = 0

    def init(self):
        for backend in self.backends:
            pass

    def run(self):
        """
        Returns the sum of unread messages across all registered backends
        """
        unread = 0
        current_unread = 0
        for id, backend in enumerate(self.backends):
            temp = backend.unread
            unread = unread + backend.unread
            if id == self.current_backend:
                current_unread = temp

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

        account_name = getattr(self.backends[self.current_backend], "account", "No name")

        self.output = {
            "full_text": format.format(unread=unread, current_unread=current_unread, account=account_name),
            "urgent": urgent,
            "color": color,
        }

    def scroll_backend(self, step):
        self.current_backend = (self.current_backend + step) % len(self.backends)

    def open_client(self):
        if self.email_client:
            retcode, _, stderr = run_through_shell(self.email_client)
            if retcode != 0 and stderr:
                self.logger.error(stderr)
