import xml.etree.ElementTree as ET
from i3pystatus import IntervalModule
from urllib.request import urlopen


class Plexstatus(IntervalModule):
    """
    Displays what is currently being streamed from your Plex Media Server.
    """

    settings = (
        ("apikey", "Your Plex API authentication key "
         "(https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-"
         "account-token-X-Plex-Token) ."),
        ("address", "Hostname or IP address of the Plex Media Server."),
        ("port", "Port which Plex Media Server is running on."),
        ("interval", "Update interval (in seconds)."),
        ("format_no_streams", "String that is shown if nothing is being "
         "streamed."),
        "format"
    )
    required = ("apikey", "address")
    color = "#00FF00"  # green
    no_stream_color = "#FF0000"  # red
    port = 32400
    interval = 120
    format_no_streams = None
    format = "{platform}: {title}"

    def run(self):
        PMS_URL = '%s%s%s%s' % ('http://', self.address, ':', self.port)
        PMS_STATUS_URI = '/status/sessions/?X-Plex-Token='
        PMS_STATUS_URL = PMS_URL + PMS_STATUS_URI + self.apikey
        response = urlopen(PMS_STATUS_URL)
        xml_response = response.read()
        tree = ET.fromstring(xml_response)

        cdict = {'title': '',
                 'platform': ''}

        for vid in tree.iter('Video'):
            try:
                cdict['title'] = vid.attrib['title']
            except AttributeError:
                pass

        for play in tree.iter('Player'):
            try:
                cdict['platform'] = play.attrib['platform']
            except AttributeError:
                pass

        self.data = cdict
        if not cdict['title'] or not cdict['platform']:
            self.output = {} if not self.format_no_streams else {
                "full_text": self.format_no_stream,
                "color": self.no_stream_color
            }
        else:
            self.output = {
                "full_text": self.format.format(**cdict),
                "color": self.color
            }
