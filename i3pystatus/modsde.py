#!/usr/bin/env python

import urllib.request
import urllib.parse
import urllib.error
import re
import http.cookiejar
import xml.etree.ElementTree as ET
import webbrowser

from i3pystatus import IntervalModule


class ModsDeChecker(IntervalModule):
    """
    This class returns i3status parsable output of the number of
    unread posts in any bookmark in the mods.de forums.
    """

    settings = (
        ("format",
         """Use {unread} as the formatter for number of unread posts"""),
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
        ("offset", """subtract number of posts before output"""),
        "color", "username", "password"
    )
    required = ("username", "password")
    keyring_backend = None

    color = "#7181fe"
    offset = 0
    format = "{unread} new posts in bookmarks"

    login_url = "http://login.mods.de/"
    bookmark_url = "http://forum.mods.de/bb/xml/bookmarks.php"
    opener = None
    cj = None
    logged_in = False

    on_leftclick = "open_browser"

    def init(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj))

    def run(self):
        unread = self.get_unread_count()

        if not unread:
            self.output = None
        else:
            self.output = {
                "full_text": self.format.format(unread=unread),
                "urgent": "true",
                "color": self.color
            }

    def get_unread_count(self):
        if not self.logged_in:
            self.login()

        try:
            f = self.opener.open(self.bookmark_url)
            root = ET.fromstring(f.read())
            return int(root.attrib["newposts"]) - self.offset
        except Exception:
            self.cj.clear()
            self.opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self.cj))
            self.logged_in = False

    def login(self):
        data = urllib.parse.urlencode({
            "login_username": self.username,
            "login_password": self.password,
            "login_lifetime": "31536000"
        })

        try:
            response = self.opener.open(self.login_url, data.encode("ascii"))
        except Exception:
            return

        page = response.read().decode("ISO-8859-15")

        m = re.search("http://forum.mods.de/SSO.php[^']*", page)
        self.cj.clear()

        if m and m.group(0):
            # get the cookie
            response = self.opener.open(m.group(0))
            for cookie in self.cj:
                self.cj.clear
                self.logged_in = True
                self.opener.addheaders.append(
                    ("Cookie", "{}={}".format(cookie.name, cookie.value)))
            return True
        return False

    def open_browser(self):
        webbrowser.open_new_tab("http://forum.mods.de/bb/")
