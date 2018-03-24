from i3pystatus import Module

import random
import string
import subprocess


class RandomPassword(Module):
    """
    Generates a random password and copies it to the clipboard. Useful if you use any password manager and you want to generate a password in the moment and save it later in you manager's database.

    Uses `SystemRandom` class as a cryptographically secure pseudo-number generator - <https://docs.python.org/3/library/random.html#random.SystemRandom>

    - Requires `xsel` or `xclip` for copying to the clipboard.
    - Generates a new password with a left click by default.
    - Generates a password with a default length of 12 and with lowercase, uppercase,  digits and special symbols.

    .. rubric:: Available formatters

    * `{length}` — length of generated password
    """

    settings = (
        ("format", "Format string to be displayed in the status bar"),
        ("length", "Length of the generated password"),
        ("charset", "Dictionary containing character types to be included in the password"),
        ("cliptool", "Currently supports xsel and xclip"),
        ("color", "HTML color hex code #RRGGBB"),
    )

    format = ''
    length = 12
    charset = ['lowercase', 'uppercase', 'digits', 'special']
    cliptool = None
    color = None

    on_doubleleftclick = 'generate_password'

    def init(self):
        # Finds out if either xsel or xclip exist
        self._find_cliptool()

        cdict = {
            'length': self.length
        }

        self.output = {
            "full_text": self.format.format(**cdict)
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
        if 'lowercase' in self.charset:
            chars = string.ascii_lowercase
        if 'uppercase' in self.charset:
            chars += string.ascii_uppercase
        if 'digits' in self.charset:
            chars += string.digits
        if 'special' in self.charset:
            chars += string.punctuation

        passwd = ''.join(random.SystemRandom().choice(chars) for x in range(self.length))

        p = subprocess.Popen([self.cliptool, self._clip_params[0], self._clip_params[1]], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=passwd.encode('utf-8'))
