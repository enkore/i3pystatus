#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
from datetime import datetime,timedelta
import imaplib
from statushandler import has_internet_connection


class MailChecker(object):
    """ 
    This class handles mailservers and outputs i3status compatible
    json data for the accumulated unread count. The mail server
    functionality is implemented in the subclass MailChecker.MailServer
    """
    
    settings =  {
        'color': '#ff0000',
        'servers': []
    }

    servers = []

    def __init__(self, settings = None):
        self.settings.update(settings)

        for server in settings['servers']:
            srv = MailChecker.MailServer(server)
            self.servers.append(srv)

    def output(self):
        unread = 0
        for srv in self.servers:
            unread += srv.get_unread_count()

        if not unread:
            return None

        return {'full_text' : '%d new email%s' % (unread, ('s' if unread > 1 else '')), 
                'name' : 'newmail',
                'urgent' : 'true',
                'color' : self.settings['color']}

    class MailServer:
        """ 
        This class provides the functionality to connect
        to a mail server and fetch the count of unread emails.
        When the server connection is lost, it returns 0 and
        tries to reconnect. It checks every 'pause' seconds.
        """

        host = ""
        port = ""
        imap_class = imaplib.IMAP4
        username = ""
        password = ""
        connection = None
        pause = 30
        unread_cache = 0
        last_checked = datetime.now()

        def __init__(self, settings_dict):
            self.host = settings_dict['host']
            self.port = settings_dict['port']
            self.username = settings_dict['username']
            self.password = settings_dict['password']
            self.pause = settings_dict['pause']

            if settings_dict['ssl']:
                self.imap_class = imaplib.IMAP4_SSL

            self.last_checked = \
                datetime.now() - timedelta(seconds=self.pause)

        def get_connection(self):
            if not has_internet_connection():
                self.connection = None
            else:
                if not self.connection:
                    try:
                        self.connection = self.imap_class(self.host, self.port)
                        self.connection.login(self.username, self.password)
                        self.connection.select()
                    except Exception:
                        self.connection = None

                try:
                    self.connection.select()
                except Exception as e:
                    self.connection = None

            return self.connection

        def get_unread_count(self):
            delta = datetime.now() - self.last_checked

            if delta.total_seconds() > self.pause:
                unread = 0
                conn = self.get_connection()
                if conn:
                    unread += len(conn.search(None,'UnSeen')[1][0].split())
                
                self.unread_cache = unread
                self.last_checked = datetime.now()

            return self.unread_cache
