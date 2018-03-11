from i3pystatus import Module
import random
import string
import subprocess

class Password(Module):
    """
    Generates a random password and copies it to clipboard.
    """

    settings = (
        "text",
        ("length", "Length of the generated password"),
        ("characters", "Character set used to generate a new password"),
        ("color", "HTML color hex code #RRGGBB"),
    )

    text = 'test'
    length = 12
    uppercase = True
    digits = False
    color = None

    on_leftclick = "generate"

    def init(self):
        p = subprocess.Popen(['xclip', '-selection', 'c'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input='test'.encode('utf-8'))

        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color

    def generate(self):
        # chars = string.ascii_lowercase
        # if self.uppercase: chars += string.ascii_uppercase
        # if self.digits: chars += string.digits
        # passwd = ''.join(random.SystemRandom.choice(chars) for x in range(self.length))
        pass
