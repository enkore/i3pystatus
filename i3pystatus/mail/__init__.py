
from i3pystatus import SettingsBase, IntervalModule

class Backend(SettingsBase):
    """Handle the details of checking for mail"""

    unread = 0
    """Return number of unread mails

    You'll probably implement that as a property"""

class Mail(IntervalModule):
    settings = ("backends", "color",)
    required = ("backends",)

    def run(self):
        unread = sum(lambda backend: backend.unread, self.backends)

        if (unread == 0):
            color = "#00FF00"
            urgent = "false"
        else:
            color = "#ff0000"
            urgent = "true"

        self.output = {
            "full_text" : "%d new email%s" % (unread, ("s" if unread > 1 else "")),
            "name" : "newmail",
            "urgent" : urgent,
            "color" : color
        }
