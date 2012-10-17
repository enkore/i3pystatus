#!/usr/bin/env python
# -*- coding: utf-8 -*-

# note that this needs the notmuch python bindings. For more info see:
# http://notmuchmail.org/howto/#index4h2
import notmuch
import json

class NotmuchMailChecker(object):
    """ 
    This class checks for the number of unread messages in the notmuch
    database using the notmuch python bindings
    """
    
    settings =  {
        'color': '#ff0000',
        'servers': []
    }

    db_path = ''

    servers = []

    def __init__(self, db_path):
        self.db_path = db_path

    def output(self):
        db = notmuch.Database(self.db_path)
        unread = notmuch.Query(db, 'tag:unread and tag:inbox').count_messages()
        
        if (unread == 0):
            color = '#00FF00'
            urgent = 'false'
        else:
            color = '#ff0000',
            urgent = 'true'

        return {'full_text' : '%d new email%s' % (unread, ('s' if unread > 1 else '')), 
                'name' : 'newmail',
                'urgent' : urgent,
                'color' : color }
