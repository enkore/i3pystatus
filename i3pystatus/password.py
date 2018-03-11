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
        # ("lowercase", "Generate passwords with lowercase characters"),
        # ("uppercase", "Generate passwords with uppercase characters"),
        # ("digits", "Generate passwords with digits"),
        # ("special", "Generate passwords with special characters"),
        ("color", "HTML color hex code #RRGGBB"),
        ("charset", "Dictionary containing settings"),
    )

    text = ''
    length = 12
    charset = ['lowercase', 'uppercase', 'digits', 'special']
    color = None

    on_doubleleftclick = 'generate_password'

    def init(self):
        if self._cliptool_exists('xsel'): self.cliptool = 'xsel'
        elif self._cliptool_exists('xclip'): self.cliptool = 'xclip'

        assert self.cliptool, 'It was no possible to find xsel or xclip installed in your system.'

        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color

    def _cliptool_exists(self, tool):
        return subprocess.call(['which', tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

    def _xsel_copy(self, text):
        p = subprocess.Popen(['xsel', '-b', '-i'], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode('utf-8'))

    def _xclip_copy(self, text):
        p = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode('utf-8'))

    def generate_password(self):
        # If a blank list is provided for the charset, it will generate an empty password
        chars = ''
        if 'lowercase' in self.charset: chars = string.ascii_lowercase
        if 'uppercase' in self.charset: chars += string.ascii_uppercase
        if 'digits' in self.charset: chars += string.digits
        if 'special' in self.charset: chars += string.punctuation

        passwd = ''.join(random.SystemRandom().choice(chars) for x in range(self.length))
        if self.cliptool == 'xsel': self._xsel_copy(passwd)
        elif self.cliptool == 'xclip': self._xclip_copy(passwd)

