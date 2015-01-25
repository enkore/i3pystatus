import os

__author__ = 'facetoe'
from keyring.backend import KeyringBackend


# This is an example custom keyring backend. It should probably be somewhere else...
class NetrcBackend(KeyringBackend):
    def get_password(self, service, username):
        from netrc import netrc
        sections = service.split('.')
        setting = sections[-1]
        if setting == 'password':
            key = ".".join(sections[:-1])
            setting_tuple = netrc().authenticators(key)
            if setting_tuple:
                login, account, password = setting_tuple
                return password

    def set_password(self, service, username, password):
        raise Exception("Setting password not supported!")

    def priority(cls):
        netrc_path = os.path.isfile(os.path.expanduser("~/.netrc"))
        if not os.path.isfile(netrc_path):
            raise Exception("No .netrc found at: %s" % netrc_path)
        return 0.5
