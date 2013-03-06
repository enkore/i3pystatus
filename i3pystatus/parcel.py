
from urllib.request import urlopen

import lxml.html
from lxml.cssselect import CSSSelector

from i3pystatus import IntervalModule

class TrackerAPI:
    def __init__(self, idcode):
        pass

    def status(self):
        return {}

class DHL(TrackerAPI):
    URL="http://nolp.dhl.de/nextt-online-public/set_identcodes.do?lang=en&idc={idcode}"
    def __init__(self, idcode):
        self.idcode = idcode
        self.url = self.URL.format(idcode=self.idcode)

        self.progress_selector = CSSSelector(".greyprogressbar > span, .greenprogressbar > span")
        self.last_status_selector = CSSSelector(".events .eventList tr")
        self.intrarow_status_selector = CSSSelector("td.status div")

    def status(self):
        ret = {}
        with urlopen(self.url) as page:
            page = lxml.html.fromstring(page.read())
            ret["progress"] = self.progress_selector(page)[0].text.strip()
            last_row = self.last_status_selector(page)[-1]
            ret["status"] = self.intrarow_status_selector(last_row)[0].text.strip()
        return ret

class ParcelTracker(IntervalModule):
    interval = 20

    settings = (
        ("instance", "Tracker instance"),
        "format",
        "name",
    )
    required = ("instance",)

    format = "{name}:{progress}"

    def run(self):
        fdict = {
            "name": self.name,
        }
        fdict.update(self.instance.status())

        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "instance": self.name,
        }
