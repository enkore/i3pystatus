import exchangelib
import contextlib
import time

from i3pystatus.mail import Backend


EWS_EXCEPTIONS = (Exception)


class EWS(Backend):
    """
    Checks for mail on an Exchange account.

    Requires the python exchangelib library - https://github.com/ecederstrand/exchangelib.
    """

    settings = (
        ("host", 'The url to connect to. If unset, autodiscover is tried with the email address domain. If set, autodiscover is disabled.'),
        "username", "password", "email_address",
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
    )
    required = ("username", "password", "email_address")
    keyring_backend = None

    host = None

    account = None
    last = 0

    @contextlib.contextmanager
    def ensure_connection(self):
        try:
            if not self.account:
                credentials = exchangelib.ServiceAccount(
                    username=self.username,
                    password=self.password)
                if self.host:
                    config = exchangelib.Configuration(
                        server=self.host,
                        credentials=credentials)
                    self.account = exchangelib.Account(
                        primary_smtp_address=self.email_address,
                        config=config,
                        autodiscover=False,
                        access_type=exchangelib.DELEGATE)
                else:
                    self.account = exchangelib.Account(
                        primary_smtp_address=self.email_address,
                        credentials=credentials,
                        autodiscover=True,
                        access_type=exchangelib.DELEGATE)
            yield
        except EWS_EXCEPTIONS as e:
            # NOTE(sileht): retry just once if the connection have been
            # broken to ensure this is not a sporadic connection lost.
            # Like wifi reconnect, sleep wake up
            # Wait a bit when disconnection occurs to not hog the cpu
            print(e)
            time.sleep(1)
            self.connection = None

    def count_new_mail(self):
        self.account.inbox.refresh()
        self.last = self.account.inbox.unread_count

    @property
    def unread(self):
        with self.ensure_connection():
            self.count_new_mail()
        return self.last


Backend = EWS
