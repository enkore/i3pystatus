from i3pystatus import Module


class Text(Module):
    """
    Display static, colored text.
    """

    settings = (
        "text",
        ("color", "HTML color code #RRGGBB"),
    )
    required = ("text",)

    color = None

    def init(self):
        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color
