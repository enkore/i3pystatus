#!/usr/bin/env python
# -*- coding: utf-8 -*-

# note that this needs the notmuch python bindings. For more info see:
# http://notmuchmail.org/howto/#index4h2
import notmuch
import json

from i3pystatus import IntervalModule

class NotmuchMailChecker(IntervalModule):
    """ 
    This class uses the notmuch python bindings to check for the
    number of messages in the notmuch database with the tags "inbox"
    and "unread"
    """
    
    db_path = ''

    def __init__(self, db_path):
        self.db_path = db_path

    def run(self):
        db = notmuch.Database(self.db_path)
        unread = notmuch.Query(db, 'tag:unread and tag:inbox').count_messages()
        
        if (unread == 0):
            color = '#00FF00'
            urgent = 'false'
        else:
            color = '#ff0000'
            urgent = 'true'

        return {'full_text' : '%d new email%s' % (unread, ('s' if unread > 1 else '')), 
                'name' : 'newmail',
                'urgent' : urgent,
                'color' : color }
