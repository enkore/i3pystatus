import sys
import imaplib

from i3pystatus.mail import Backend
from i3pystatus.core.util import internet


class IMAP(Backend):
    """
    Checks for mail on a IMAP server
    """

    settings = (
        "host", "port",
        "username", "password",
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
        "ssl",
        "mailbox",
    )
    required = ("host", "username", "password")
    keyring_backend = None

    port = 993
    ssl = True
    mailbox = "INBOX"

    imap_class = imaplib.IMAP4
    connection = None
    last = 0

    def init(self):
        if self.ssl:
            self.imap_class = imaplib.IMAP4_SSL

    def get_connection(self):
        if not self.connection:
            self.connection = self.imap_class(self.host, self.port)
            self.connection.login(self.username, self.password)
            self.connection.select(self.mailbox)

        self.connection.select(self.mailbox)

        return self.connection

    @property
    def unread(self):
        if internet():
            conn = self.get_connection()
            self.last = len(conn.search(None, "UnSeen")[1][0].split())
        return self.last


Backend = IMAP
