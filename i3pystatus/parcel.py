
from urllib.request import urlopen
import webbrowser

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

        error_selector = CSSSelector("#set_identcodes .error")
        self.error = lambda page: len(error_selector(page)) >= 1
        self.progress_selector = CSSSelector(".greyprogressbar > span, .greenprogressbar > span")
        self.last_status_selector = CSSSelector(".events .eventList tr")
        self.intrarow_status_selector = CSSSelector("td.status div")

    def status(self):
        ret = {}
        with urlopen(self.url) as page:
            page = lxml.html.fromstring(page.read())
            if self.error(page):
                ret["progress"] = ret["status"] = "n/a"
            else:
                ret["progress"] = self.progress_selector(page)[0].text.strip()
                last_row = self.last_status_selector(page)[-1]
                ret["status"] = self.intrarow_status_selector(last_row)[0].text.strip()
        return ret

    def get_url(self):
        return self.url

class UPS(TrackerAPI):
    URL="http://wwwapps.ups.com/WebTracking/processRequest?HTMLVersion=5.0&Requester=NES&AgreeToTermsAndConditions=yes&loc=en_US&tracknum={idcode}"

    def __init__(self, idcode):
        self.idcode = idcode
        self.url = self.URL.format(idcode=self.idcode)

        error_selector = CSSSelector(".secBody .error")
        self.error = lambda page: len(error_selector(page)) >= 1
        self.status_selector = CSSSelector("#tt_spStatus")
        self.progress_selector = CSSSelector(".pkgProgress div")

    def status(self):
        ret = {}
        with urlopen(self.url) as page:
            page = lxml.html.fromstring(page.read())
            if self.error(page):
                ret["progress"] = ret["status"] = "n/a"
            else:
                ret["status"] = self.status_selector(page)[0].text.strip()
                progress_cls = int(int(self.progress_selector(page)[0].get("class").strip("staus")) / 5 * 100)
                ret["progress"]  = progress_cls
        return ret

    def get_url(self):
        return self.url

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

    def on_leftclick(self):
        webbrowser.open_new_tab(self.instance.get_url())
