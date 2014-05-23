from urllib.request import urlopen
import webbrowser

import lxml.html
from lxml.cssselect import CSSSelector
from bs4 import BeautifulSoup as BS

from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require


class TrackerAPI:
    def __init__(self, idcode):
        pass

    def status(self):
        return {}


class DHL(TrackerAPI):
    URL = "http://nolp.dhl.de/nextt-online-public/set_identcodes.do?lang=en&idc={idcode}"

    def __init__(self, idcode):
        self.idcode = idcode
        self.url = self.URL.format(idcode=self.idcode)

    def error(self, page):
        result = ''.join(page.xpath('//div[@class="col col-lg-12"]/h2/text()'))

        if self.idcode in result:
            return False
        return True

    def get_progress(self, page):
        elements = page.xpath('//tr[@class="mm_mailing_process "]/td/ul/li')

        for i, element in enumerate(elements, 1):
            picture_link = ''.join(element.xpath('./img/@src')).lower()

            if 'active' in picture_link:
                status = ''.join(element.xpath('./img/@alt'))

                progress = '%i' % (i / len(elements) * 100)

            elif 'default' in picture_link:
                break

        return progress, status

    def status(self):
        ret = {}
        with urlopen(self.url) as page:
            page = lxml.html.fromstring(page.read())

            if not self.error(page):
                ret["progress"] = ret["status"] = "n/a"

            else:
                progress, status = self.get_progress(page)
                ret["progress"] = progress
                ret["status"] = status

        return ret

    def get_url(self):
        return self.url


class UPS(TrackerAPI):
    URL = "http://wwwapps.ups.com/WebTracking/processRequest?HTMLVersion=5.0&Requester=NES&AgreeToTermsAndConditions=yes&loc=en_US&tracknum={idcode}"

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
                progress_cls = int(
                    int(self.progress_selector(page)[0].get("class").strip("staus")) / 5 * 100)
                ret["progress"] = progress_cls
        return ret

    def get_url(self):
        return self.url


class ParcelTracker(IntervalModule):
    """
    Used to track parcel/shipments.
    """
    interval = 20

    settings = (
        ("instance", "Tracker instance, for example ``parcel.UPS('your_id_code')``"),
        "format",
        "name",
    )
    required = ("instance",)

    format = "{name}:{progress}"

    @require(internet)
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


class Itella(IntervalModule):

    interval = 3600 # 1h

    settings = (
        ("lang", "fi, sv or en (default: fi)"),
        "name",
        "idcode",
        "format",
        "color",
    )
    required = ("idcode",)

    color = "#FFFFFF"
    format = "{name}:{progress}"
    lang = "fi"
    name = ""

    @require(internet)
    def run(self):
        try:
            page = BS(urlopen(
                "http://www.itella.fi/itemtracking/itella/search_by_shipment_id"
                "?lang={lang}&ShipmentId={s_id}".format(
                    s_id=self.idcode, lang=self.lang)
            ).read())
            events = page.find(id="shipment-event-table")
            newest = events.find(id="shipment-event-table-cell")
            status = newest.find(
                "div", {"class": "shipment-event-table-header"}
            ).text.strip()
            time, location = [
                d.text.strip() for d in
                newest.find_all("span", {"class": "shipment-event-table-data"})
            ][:2]
            progress = "{status} {time} {loc}".format(status=status, time=time, loc=location)

            self.output = {
                "full_text": self.format.format(
                    name=self.name,
                    status=status,
                    location=location,
                    time=time,
                    progress=progress,
                    ),
                "color": self.color
            }
        except Exception as e:
            self.output = {"full_text": str(e)}
