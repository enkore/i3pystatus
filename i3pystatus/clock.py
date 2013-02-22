#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, locale, datetime

from i3pystatus import IntervalModule

class Clock(IntervalModule):
    """ 
    This class shows a clock
    """
    
    def __init__(self, format_string=None):
        lang = os.environ.get('LANG', None)
        if lang:
            locale.setlocale(locale.LC_ALL, lang)
        if not format_string:
            lang = locale.getlocale()[0]
            if lang == 'en_US':
                # MDY format - United States of America
                format_string = "%a %b %-d %X"
            else:
                # DMY format - almost all other countries
                format_string = "%a %-d %b %X"
        self.format_string = format_string

    def run(self):
        full_text = datetime.datetime.now().strftime(self.format_string)
        self.output = {
            "full_text": full_text,
            "name": "pyclock",
            "urgent": False,
            "color": "#ffffff"
        }
