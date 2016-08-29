try:
    from imaplib2 import IMAP4, IMAP4_SSL
    use_idle = True
except:
    from imaplib import IMAP4, IMAP4_SSL
    use_idle = False
import socket
from threading import *

from i3pystatus.mail import Backend


# This is the threading object that does all the waiting on
# the event
class Idler(object):
    def __init__(self, conn, callback, callback_reconnect):
        self.thread = Thread(target=self.idle)
        self.M = conn
        self.callback_reconnect = callback_reconnect
        self.event = Event()
        self.callback = callback

    def start(self):
        self.thread.start()

    def stop(self):
        self.event.set()

    def join(self):
        self.thread.join()

    def idle(self):

        while True:
            if self.event.isSet():
                return

            self.needsync = False

            def callback(args):
                if not self.event.isSet():
                    self.needsync = True
                    self.event.set()

            try:
                self.M.idle(callback=callback)
                self.event.wait()

                if self.needsync:
                    self.event.clear()
                    self.callback()
            except:
                break

        self.M = self.callback_reconnect()
        self.stop()
        self.start()


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

    imap_class = IMAP4
    connection = None
    last = 0

    def init(self):
        if self.ssl:
            self.imap_class = IMAP4_SSL

        self.conn = self.get_connection()

        if use_idle:
            idler = Idler(self.conn, self.count_new_mail, self.get_connection)
            idler.start()

    def get_connection(self):
        if self.connection:
            try:
                self.connection.select(self.mailbox)
            except socket.error:
                # NOTE(sileht): retry just once if the connection have been
                # broken to ensure this is not a sporadic connection lost.
                # Like wifi reconnect, sleep wake up
                try:
                    self.connection.logout()
                except socket.error:
                    pass
                self.connection = None

        if not self.connection:
            self.connection = self.imap_class(self.host, self.port)
            self.connection.login(self.username, self.password)
            self.connection.select(self.mailbox)

        return self.connection

    def count_new_mail(self):
        self.last = len(self.conn.search(None, "UnSeen")[1][0].split())

    @property
    def unread(self):
        try:
            conn = self.get_connection()
        except socket.gaierror:
            pass
        else:
            self.last = len(conn.search(None, "UnSeen")[1][0].split())
        finally:
            if not use_idle:
                self.count_new_mail()
            return self.last

Backend = IMAP
