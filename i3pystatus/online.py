from i3pystatus import IntervalModule
from i3pystatus.core.util import internet


class Online(IntervalModule):

    """Show internet connection status."""

    settings = (
        ("color", "Text color when online"),
        ('color_offline', 'Text color when offline'),
        ('format_online', 'Status text when online'),
        ('format_offline', 'Status text when offline'),
    )

    color = '#ffffff'
    color_offline = '#ff0000'
    format_online = 'online'
    format_offline = 'offline'
    interval = 10

    def run(self):
        if internet():
            self.output = {
                "color": self.color,
                "full_text": self.format_online,
            }
        else:
            self.output = {
                "color": self.color_offline,
                "full_text": self.format_offline,
            }
