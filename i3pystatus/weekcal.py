from calendar import Calendar
from datetime import date, timedelta

from i3pystatus import IntervalModule


class WeekCal(IntervalModule):
    """
    Displays the days of the current week as they would be represented on a calendar sheet,
    with the current day highlighted.
    By default, the current day of week is displayed in the front, and the month and year are
    displayed in the back.

    Example: ``Sat  16 17 18 19 20[21]22  May 2016``
    """

    settings = (
        ("startofweek", "First day of the week (0 = Monday, 6 = Sunday), defaults to 0."),
        ("prefixformat", "Prefix in strftime-format"),
        ("suffixformat", "Suffix in strftime-format"),
        ("todayhighlight", "Characters to highlight today's date"),
    )
    startofweek = 0
    interval = 30
    prefixformat = "%a"
    suffixformat = "%b %Y"
    todayhighlight = ("[", "]")

    def __init__(self, *args, **kwargs):
        IntervalModule.__init__(self, *args, **kwargs)
        self.cal = Calendar(self.startofweek)

    def run(self):
        today = date.today()
        yesterday = today - timedelta(days=1)

        outstr = today.strftime(self.prefixformat) + " "

        weekdays = self.cal.iterweekdays()
        if today.weekday() == self.startofweek:
            outstr += self.todayhighlight[0]
        else:
            outstr += " "

        nextweek = False  # keep track of offset if week doesn't start on monday

        for w in weekdays:
            if w == 0 and self.startofweek != 0:
                nextweek = True
            if nextweek and today.weekday() >= self.startofweek:
                w += 7
            elif not nextweek and today.weekday() < self.startofweek:
                w -= 7

            weekday_offset = today.weekday() - w
            weekday_delta = timedelta(days=weekday_offset)
            weekday = today - weekday_delta
            if weekday == yesterday:
                outstr += weekday.strftime("%d") + self.todayhighlight[0]
            elif weekday == today:
                outstr += weekday.strftime("%d") + self.todayhighlight[1]
            else:
                outstr += weekday.strftime("%d ")

        outstr += " " + today.strftime(self.suffixformat)

        self.output = {
            "full_text": outstr,
            "urgent": False,
        }
