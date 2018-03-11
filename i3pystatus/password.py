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
        ("charset", "Dictionary containing settings"),
        ("color", "HTML color hex code #RRGGBB"),
        ("cliptool", "Dictionary containing settings"),
    )

    text = ''
    length = 12
    charset = ['lowercase', 'uppercase', 'digits', 'special']
    cliptool = None
    color = None

    on_doubleleftclick = 'generate_password'

    def init(self):
        # Finds out if either xsel or xclip exist
        self._find_cliptool()

        self.output = {
            "full_text": self.text
        }
        if self.color:
            self.output["color"] = self.color

    def _find_cliptool(self):
        if subprocess.call(['which', 'xsel'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            self.cliptool = 'xsel'
            self._clip_params = ['-b', '-i']
        elif subprocess.call(['which', 'xclip'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            self.cliptool = 'xclip'
            self._clip_params = ['-selection', 'c']

        # Asserts that either xsel or xclip was found
        assert self.cliptool and self._clip_params, 'It was no possible to find xsel or xclip installed in your system.'

    def generate_password(self):
        # If a blank list is provided for the charset, it will generate an empty password
        chars = ''
        if 'lowercase' in self.charset: chars = string.ascii_lowercase
        if 'uppercase' in self.charset: chars += string.ascii_uppercase
        if 'digits' in self.charset: chars += string.digits
        if 'special' in self.charset: chars += string.punctuation

        passwd = ''.join(random.SystemRandom().choice(chars) for x in range(self.length))

        p = subprocess.Popen([self.cliptool, self._clip_params[0], self._clip_params[1]], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=passwd.encode('utf-8'))

