#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Fedor Marchenko"
__email__ = "mfs90@mail.ru"
__date__ = "Dec 25, 2014"

from i3pystatus import IntervalModule
import imaplib
import email
import datetime
from itertools import groupby
from functools import reduce
from lxml import html
import os
import re
import json


def datekeyfn(msg):
    date_tuple = email.utils.parsedate_tz(msg['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        return local_date
    return None


def time2float(strtime):
    if not strtime:
        return 0.0
    h, m = strtime.split(':')
    return float(h or 0) + float(m or 0) / 60


class Tcchk(IntervalModule):
    interval = 3600
    format = u"\u231b: {time}"
    host = None
    login = None
    password = None
    folder = '"TIMECARD REPORT"'
    date = None

    settings = ("host", "login", "password", "format", "date", "calendar_times_json")

    require = ("host", "login", "password")

    def __init__(self, *args, **kwargs):
        super(Tcchk, self).__init__(*args, **kwargs)
        if not self.date:
            self.date = datetime.date.today()

    def run(self):
        self.output = {
            "color": "#ffee66"
        }
        formatstr = "%Y%m%d-AM" if datetime.datetime.today().hour < 15 else "%Y%m%d-PM"

        timepath = '/tmp/%s-tcchk' % datetime.datetime.today().strftime(formatstr)
        if os.path.exists(timepath):
            with open(timepath, 'r') as f:
                self.output["full_text"] = self.format.format(time=f.readline())
                # return

        m = imaplib.IMAP4(self.host, 143)
        m.login(self.login, self.password)
        m.select(self.folder)
        result, data = m.uid('search', None, "ALL")

        mail_list = []

        if result == "OK":
            for num in data[0].split():
                result, data = m.uid('fetch', num, '(RFC822)')
                if result == 'OK':
                    email_message = email.message_from_bytes(data[0][1])
                    mail_list.append(email_message)

        mail_list.sort(key=datekeyfn, reverse=True)
        mail_list = filter(lambda m: datekeyfn(m).month == self.date.month and datekeyfn(m).day != 1, mail_list)

        times = []

        for key, valuesiter in groupby(mail_list, key=lambda m: m['Subject']):
            for msg in valuesiter:
                body = msg.get_payload()
                if not isinstance(body, (str,)):
                    body = body[1].get_payload()
                root = html.fromstring(body)

                for time_tr in root.xpath("//table[4]/tr"):
                    f_time = 0.0
                    if len(time_tr.xpath("./td[2]/text()")):
                        date_p = re.compile("\d{1,2}/\d{1,2}/\d{1,2}")
                        date_text = time_tr.xpath("./td[2]/text()")[0]

                        if date_p.match(date_text):
                            date = datetime.datetime.strptime(date_text, "%m/%d/%y")

                            if date.month == self.date.month and date.year == self.date.year:
                                f_time = time2float(time_tr.xpath("./td/text()")[-2].strip())
                                if f_time == 0:
                                    f_time = get_next_tr_time(time_tr)
                                times.append(f_time)
                                # print(date, time2float(time_tr.xpath("./td/text()")[-2].strip()))

                # try:
                #     time = time2float(root.xpath("//td[contains(text(), 'Total Hours')]/following-sibling::td[1]/text()")[0])
                # except IndexError as ex:
                #     time = 0
                # times.append(time)

                break

        m.close()
        m.logout()

        try:
            total_hours = reduce(lambda x, y: x + y, times)
        except TypeError as ex:
            total_hours = 0.0

        with open(timepath, 'w+') as f:
            f.write(str(round(total_hours, 2)))

        self.output["full_text"] = self.format.format(time=round(total_hours, 2))

        if self.calendar_times_json and os.path.exists(self.calendar_times_json):
            mt = []
            with open(self.calendar_times_json, "r") as in_file:
                mt = json.load(in_file)
            tdiff = round(total_hours, 2) - int(mt[self.date.month - 1]["time"])
            self.output["full_text"] = "{} | {}".format(self.output["full_text"], tdiff)
            if tdiff >= 0:
                self.output["color"] = "#19d100"
            else:
                self.output["color"] = "#ff384f"
            with open(timepath, 'w+') as f:
                f.write("{} | {}".format(round(total_hours, 2), tdiff))

        return


def get_next_tr_time(tr):
    f_time = 0
    if tr.get("bgcolor") in tr.xpath("./following-sibling::tr[1]/@bgcolor"):
        f_time = time2float(tr.xpath("./following-sibling::tr[1]/td/text()")[-2].strip())
        if f_time == 0:
            f_time = get_next_tr_time(tr.xpath("./following-sibling::tr[@bgcolor='%s'][1]" % tr.get("bgcolor"))[0])
    return f_time
