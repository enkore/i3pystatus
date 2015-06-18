import sys
from i3pystatus.mail import Backend
import subprocess


class MboxMail(Backend):
    """
    Checks for local mail in mbox
    """

    settings = ()
    required = ()

    @property
    def unread(self):
        p = subprocess.Popen(['messages.mailutils'], stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf8')
        assert p.returncode == 0, "messages.mailutils returned non-zero return code"
        s_stuff, message_number = stdout.strip().rsplit(':', 1)
        return int(message_number.strip())


Backend = MboxMail
