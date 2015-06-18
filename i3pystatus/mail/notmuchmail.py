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
        ("query", "Same query notmuch would accept, by default 'tag:unread and tag:inbox'"),
    )

    db_path = None
    query = "tag:unread and tag:inbox"

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

    @property
    def unread(self):
        db = notmuch.Database(self.db_path)
        result = notmuch.Query(db, self.query).count_messages()
        db.close()
        return result


Backend = Notmuch
