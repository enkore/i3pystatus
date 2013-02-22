#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
from datetime import datetime,timedelta
import imaplib

from i3pystatus import IntervalModule

class MailChecker(IntervalModule):
    """ 
    This class handles mailservers and outputs i3status compatible
    json data for the accumulated unread count. The mail server
    functionality is implemented in the subclass MailChecker.MailServer
    """
    
    settings = ("color", "servers")
    required = ("servers",)
    color = "#ff0000"

    def init(self):
        self.server_list = list(map(MailChecker.MailServer, self.servers))

    def run(self):
        unread = sum(map(lambda server: server.get_unread_count(), self.server_list))

        if unread:
            self.output = {
                "full_text" : "%d new email%s" % (unread, ("s" if unread > 1 else "")), 
                "name" : "newmail",
                "urgent" : "true",
                "color" : self.color
            }

    class MailServer:
        """ 
        This class provides the functionality to connect
        to a mail server and fetch the count of unread emails.
        When the server connection is lost, it returns 0 and
        tries to reconnect. It checks every "pause" seconds.
        """

        imap_class = imaplib.IMAP4
        connection = None

        def __init__(self, settings_dict):
            self.__dict__.update(settings_dict)

            if self.ssl:
                self.imap_class = imaplib.IMAP4_SSL

        def get_connection(self):
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
            unread = 0
            conn = self.get_connection()
            if conn:
                unread += len(conn.search(None,"UnSeen")[1][0].split())

            return unread
