from i3pystatus import Module

class Password(Module):
    """
    Generates a random password and copies it to clipboard.
    """

    settings = (
        "text",
        ("color", "HTML color hex code #RRGGBB"),
    )

    text = 'test'
    color = None

    def init(self):
        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color

    def generate(self):
        pass
