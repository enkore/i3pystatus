#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, locale, datetime

from i3pystatus import IntervalModule

class Clock(IntervalModule):
    """ 
    This class shows a clock
    """

    settings = ("format",)
    format = None

    def init(self):
        if self.format is None:
            #
            # WARNING
            # i3bar does something with the locale, wich probably
            # crashes i3pystatus when the code block below is run.
            # I don't know how to debug i3bar (I doubt it has any
            # debugging facilities).
            #
            # If your i3bar stays blank after enabling clock, well,
            # just set the format string and it should work :-)
            #

            lang = os.environ.get('LANG', None)
            if lang:
                locale.setlocale(locale.LC_ALL, lang)
            lang = locale.getlocale()[0]
            if lang == 'en_US':
                # MDY format - United States of America
                self.format = "%a %b %-d %X"
            else:
                # DMY format - almost all other countries
                self.format = "%a %-d %b %X"

    def run(self):
        full_text = datetime.datetime.now().strftime(self.format)
        self.output = {
            "full_text": full_text,
            "name": "pyclock",
            "urgent": False,
            "color": "#ffffff"
        }
