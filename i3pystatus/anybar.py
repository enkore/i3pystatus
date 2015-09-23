import threading
import socket

from i3pystatus import IntervalModule


class AnyBar(IntervalModule):
    """
    This module shows dot with given color in your panel.
    What color means is up to you. When to change color is also up to you.
    It's a port of https://github.com/tonsky/AnyBar to i3pystatus.
    Color can be changed by sending text to UDP port.
    Check the original repo how to do it.
    """

    colors = {
        "black": "#444444",  # 4C4C4C
        "black_alt": "#FFFFFF",
        "blue": "#4A90E2",
        "cyan": "#27F2CB",
        "exclamation": "#DE504C",  # vary
        "green": "#80EB0C",
        "orange": "#FF9F00",
        "purple": "#9013FE",
        "question": "#4C4C4C",  # vary
        "question_alt": "#FFFFFF",
        "red": "#CF0700",
        "white": "#4C4C4C",  # border
        "white_alt": "#FFFFFF",
        "yellow": "#FFEC00",
    }
    color = '#444444'
    port = 1738
    interval = 1

    settings = (
        ("port", "UDP port to listen"),
        ("color", "initial color"),
    )

    def main_loop(self):
        """ Mainloop blocks so we thread it."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = int(getattr(self, 'port', 1738))
        sock.bind(('127.0.0.1', port))
        while True:
            data, addr = sock.recvfrom(512)
            color = data.decode().strip()
            self.color = self.colors.get(color, color)

    def init(self):
        try:
            t = threading.Thread(target=self.main_loop)
            t.daemon = True
            t.start()
        except Exception as e:
            self.output = {
                "full_text": "Error creating new thread!",
                "color": "#AE2525"
            }

    def run(self):
        self.output = {
            "full_text": "●",
            "color": self.color
        }
