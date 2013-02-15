#!/usr/bin/env python

import sys
import json
import time
import threading
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import re
import http.cookiejar
import xml.etree.ElementTree as ET

from i3pystatus import IntervalModule

class ModsDeChecker(IntervalModule):
    """ 
    This class returns i3status parsable output of the number of
    unread posts in any bookmark in the mods.de forums.
    """

    login_url = "http://login.mods.de/"
    bookmark_url = "http://forum.mods.de/bb/xml/bookmarks.php"
    opener = None
    cj = None
    logged_in = False
    
    settings =  {
        "color": "#7181fe",
        "offset": 0,
        "format": "%d new posts in bookmarks"
    }

    def __init__(self, settings = None):
        self.settings.update(settings)
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def run(self):
        unread = self.get_unread_count()

        if not unread:
            self.output = None
        else:
            self.output = {
                "full_text" : self.settings["format"] % unread, 
                "name" : "modsde",
                "urgent" : "true",
                "color" : self.settings["color"]
            }

    def get_unread_count(self):
        if not self.logged_in:
            self.login()

        try:
            f = self.opener.open(self.bookmark_url)
            root = ET.fromstring(f.read())
            return int(root.attrib["newposts"]) - self.settings["offset"]
        except Exception:
            self.cj.clear()
            self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
            self.logged_in = False

    def login(self):
        data = urllib.parse.urlencode({
            "login_username": self.settings["username"],
            "login_password": self.settings["password"],
            "login_lifetime": "31536000"
        })

        response = self.opener.open(self.login_url, data.encode("ascii"))
        m = re.search("http://forum.mods.de/SSO.php[^']*", response.read().decode("ISO-8859-15"))
        self.cj.clear()

        if m and m.group(0):
            # get the cookie
            response = self.opener.open(m.group(0))
            for cookie in self.cj:
                self.cj.clear
                self.logged_in = True
                self.opener.addheaders.append(("Cookie", "{}={}".format(cookie.name, cookie.value)))
                return True
