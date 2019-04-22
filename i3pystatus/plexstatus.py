import xml.etree.ElementTree as ET
from i3pystatus import IntervalModule
from urllib.request import urlopen


class Plexstatus(IntervalModule):
    """
    Displays what is currently being streamed from your Plex Media Server.

    If you dont have an apikey you will need to follow this
        https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token

    .. rubric:: Formatters

    * `{title}`       - title currently being streamed
    * `{platform}`    - plex recognised platform of the streamer
    * `{product}`     - plex product name on the streamer (Plex Web, Plex Media Player)
    * `{address}`     - address of the streamer
    * `{streamer_os}` - operating system on the streaming device
    """

    settings = (
        "format",
        "color",
        ("apikey", "Your Plex API authentication key"),
        ("address", "Hostname or IP address of the Plex Media Server"),
        ("port", "Port which Plex Media Server is running on"),
        ("interval", "Update interval"),
        ("stream_divider", "divider between stream info when multiple streams are active"),
        ("format_no_streams", "String that is shown if nothing is being streamed"),
    )
    required = ("apikey", "address")
    color = "#00FF00"  # green
    no_stream_color = "#FF0000"  # red
    port = 32400
    interval = 120
    format_no_streams = None
    format = "{platform}: {title}"
    stream_divider = '-'

    def run(self):
        PMS_URL = '%s%s%s%s' % ('http://', self.address, ':', self.port)
        PMS_STATUS_URI = '/status/sessions/?X-Plex-Token='
        PMS_STATUS_URL = PMS_URL + PMS_STATUS_URI + self.apikey
        response = urlopen(PMS_STATUS_URL)
        xml_response = response.read()
        tree = ET.fromstring(xml_response)

        streams = []
        for vid in tree.iter('Video'):
            info = {'title': '',
                    'platform': '',
                    'product': '',
                    'address': '',
                    'streamer_os': ''}
            try:
                info['title'] = vid.attrib['title']
            except AttributeError as e:
                self.logger.error(e)

            for play in vid.iter('Player'):
                try:
                    info['platform'] = play.attrib['platform']
                    info['product'] = play.attrib['product']
                    info['address'] = play.attrib['address']
                    info['streamer_os'] = play.attrib['device']
                except AttributeError as e:
                    self.logger.error(e)
            streams.append(info)

        self.data = streams

        if len(streams) < 1:
            self.output = {} if not self.format_no_streams else {
                "full_text": self.format_no_streams,
                "color": self.no_stream_color
            }
        else:
            full_text = self.stream_divider.join(self.format.format(**s) for s in streams)
            self.output = {
                "full_text": full_text,
                "color": self.color
            }
