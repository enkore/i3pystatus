from i3pystatus.core.util import require, internet

try:
    from imaplib2.imaplib2 import IMAP4, IMAP4_SSL
    use_idle = True
except ImportError:
    from imaplib import IMAP4, IMAP4_SSL
    use_idle = False
import contextlib
import time
import socket
import base64
from threading import Thread

from i3pystatus.mail import Backend


IMAP_EXCEPTIONS = (socket.error, socket.gaierror, IMAP4.abort, IMAP4.error)


class IMAPGSSMixin(object):
    def gss_cb(self,challenge):
        import kerberos
        input_token = base64.b64encode(challenge).decode('utf-8')

        if self.step == 0:
            ret = kerberos.authGSSClientStep(self._gss_context, input_token)
            if ret != kerberos.AUTH_GSS_CONTINUE:
                self.step = 1
        elif self.step == 1:
            ret = kerberos.authGSSClientUnwrap(self._gss_context, input_token)
            response = kerberos.authGSSClientResponse(self._gss_context)
            ret = kerberos.authGSSClientWrap(self._gss_context, response, self.user)
        response = kerberos.authGSSClientResponse(self._gss_context)

        if response is None:
            return ""
        else:
            return base64.b64decode(response)

    def login_gssapi(self, user):
        import kerberos
        self.user = user
        self.step = 0
        _unused, self._gss_context = kerberos.authGSSClientInit("imap@{}".format(self.host))
        return self.authenticate(b"GSSAPI", self.gss_cb)


class IMAP4_SSL(IMAP4_SSL, IMAPGSSMixin):
    pass

class IMAP4(IMAP4, IMAPGSSMixin):
    pass


class IMAP(Backend):
    """
    Checks for mail on a IMAP server
    """

    settings = (
        "host", "port",
        "username", "password",
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
        "ssl",
        "gssapi",
        "mailbox",
    )
    required = ("host", "username", "password")
    keyring_backend = None

    port = 993
    ssl = True
    mailbox = "INBOX"
    gssapi = False

    imap_class = IMAP4
    connection = None
    last = 0

    def init(self):
        if self.ssl:
            self.imap_class = IMAP4_SSL

        if use_idle:
            self.thread = Thread(target=self._idle_thread)
            self.daemon = True
            self.thread.start()

    @contextlib.contextmanager
    def ensure_connection(self):
        try:
            if self.connection:
                self.connection.select(self.mailbox)
            if not self.connection:
                self.connection = self.imap_class(self.host, self.port)
                if self.gssapi:
                    self.connection.login_gssapi(self.username)
                else:
                    self.connection.login(self.username, self.password)
                self.connection.select(self.mailbox)
            yield
        except IMAP_EXCEPTIONS:
            # NOTE(sileht): retry just once if the connection have been
            # broken to ensure this is not a sporadic connection lost.
            # Like wifi reconnect, sleep wake up
            try:
                self.connection.close()
            except IMAP_EXCEPTIONS:
                pass
            try:
                self.connection.logout()
            except IMAP_EXCEPTIONS:
                pass
            # Wait a bit when disconnection occurs to not hog the cpu
            time.sleep(1)
            self.connection = None

    def _idle_thread(self):
        # update mail count on startup
        with self.ensure_connection():
            self.count_new_mail()
        while True:
            with self.ensure_connection():
                # Block until new mails
                self.connection.idle()
                # Read how many
                self.count_new_mail()

    def count_new_mail(self):
        self.last = len(self.connection.search(None, "UnSeen")[1][0].split())

    @property
    @require(internet)
    def unread(self):
        if not use_idle:
            with self.ensure_connection():
                self.count_new_mail()
        return self.last

Backend = IMAP
