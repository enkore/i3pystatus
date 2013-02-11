#!/usr/bin/env python

import sys
import json
from datetime import datetime,timedelta
import urllib, urllib2
import re
import cookielib
import xml.etree.ElementTree as ET

class ModsDeChecker(object):
    """ 
    This class returns i3status parsable output of the number of
    unread posts in any bookmark in the mods.de forums.
    """

    last_checked = datetime.now()
    unread_cache = 0
    login_url = 'http://login.mods.de/'
    bookmark_url = "http://forum.mods.de/bb/xml/bookmarks.php"
    opener = None
    cj = None
    logged_in = False
    
    settings =  {
        'color': '#7181fe',
        'pause': 20,
        'username': "",
        'password': ""
    }

    def __init__(self, settings = None):
        self.settings.update(settings)
        self.cj = cookielib.CookieJar()
        self.last_checked = \
            datetime.now() - timedelta(seconds=self.settings['pause'])
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cj))

    def get_unread_count(self):
        delta = datetime.now() - self.last_checked

        if delta.total_seconds() > self.settings['pause']:
            if not self.logged_in:
                try:
                    self.login()
                except Exception:
                    pass
            
            try:
                f = self.opener.open(self.bookmark_url)
                root = ET.fromstring(f.read())
                self.last_checked = datetime.now()
                self.unread_cache = int(root.attrib['newposts'])
            except Exception:
                self.cj.clear()
                self.opener = urllib2.build_opener(
                    urllib2.HTTPCookieProcessor(self.cj))
                self.logged_in = False

        return self.unread_cache
        

    def login(self):

        data = urllib.urlencode({
            "login_username": self.settings["username"],
            "login_password": self.settings["password"],
            "login_lifetime": "31536000"
        })

        response = self.opener.open(self.login_url, data)
        m = re.search("http://forum.mods.de/SSO.php[^']*", response.read())
        self.cj.clear()

        if m and m.group(0):
            # get the cookie
            response = self.opener.open(m.group(0))
            for cookie in self.cj:
                self.cj.clear
                self.logged_in = True
                self.opener.addheaders.append(('Cookie', 
                    '{}={}'.format(cookie.name, cookie.value)))
                return True

        return False

    def output(self):
        
        unread = self.get_unread_count()

        if not unread:
            return None

        return {'full_text' : '%d new posts in bookmarks' % unread, 
                'name' : 'modsde',
                'urgent' : 'true',
                'color' : self.settings['color']}
