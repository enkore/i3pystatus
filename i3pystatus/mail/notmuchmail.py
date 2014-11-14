#!/usr/bin/env python
# -*- coding: utf-8 -*-

# note that this needs the notmuch python bindings. For more info see:
# http://notmuchmail.org/howto/#index4h2
import notmuch
import configparser
import os
from i3pystatus.mail import Backend


class Notmuch(Backend):
    """
    This class uses the notmuch python bindings to check for the
    number of messages in the notmuch database with the tags "inbox"
    and "unread"
    """

    settings = (
        ("db_path", "Path to the directory of your notmuch database"),
    )

    db_path = None

    def init(self):
        if not self.db_path:
            defaultConfigFilename = os.path.expanduser("~/.notmuch-config")
            config = configparser.RawConfigParser()

            # read tries to read and returns successfully read filenames
            successful = config.read([
                os.environ.get("NOTMUCH_CONFIG", defaultConfigFilename),
                defaultConfigFilename
            ])

            self.db_path = config.get("database", "path")

        self.db = notmuch.Database(self.db_path)

    @property
    def unread(self):
        return notmuch.Query(self.db, "tag:unread and tag:inbox").count_messages()


Backend = Notmuch
