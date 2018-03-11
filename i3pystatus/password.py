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
        ("lowercase", "Generate passwords with lowercase characters"),
        ("uppercase", "Generate passwords with uppercase characters"),
        ("digits", "Generate passwords with digits"),
        ("special", "Generate passwords with special characters"),
        ("color", "HTML color hex code #RRGGBB"),
    )

    text = ''
    length = 12
    lowercase = True
    uppercase = True
    digits = True
    special = True
    color = None

    on_doubleleftclick = 'generate_password'

    def init(self):
        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color

    def generate_password(self):
        if self.lowercase: chars = string.ascii_lowercase
        if self.uppercase: chars += string.ascii_uppercase
        if self.digits: chars += string.digits
        if self.special: chars += string.punctuation

        passwd = ''.join(random.SystemRandom().choice(chars) for x in range(self.length))
        p = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=passwd.encode('utf-8'))

