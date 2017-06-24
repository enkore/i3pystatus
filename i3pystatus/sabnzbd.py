import json
from i3pystatus import IntervalModule
from urllib.request import urlopen


class sabnzbd(IntervalModule):
    """
    Displays the current status of SABnzbd.

    .. rubric:: Available formatters

    * All the first-level parameters from
      https://sabnzbd.org/wiki/advanced/api#queue
      (e.g. status, speed, timeleft, spaceleft, eta ...)
    """

    format = "{speed} - {timeleft}"
    format_paused = "{status}"
    host = "127.0.0.1"
    port = 8080
    api_key = ""
    url = "http://{host}:{port}/sabnzbd/api?output=json&apikey={api_key}"
    color = "#FFFFFF"
    color_paused = "#FF0000"
    color_downloading = "#00FF00"

    settings = (
        ("format", "format string used for output"),
        ("format_paused", "format string used if SABnzbd is paused"),
        ("host", "address of the server running SABnzbd"),
        ("port", "port that SABnzbd is running on"),
        ("api_key", "api key of SABnzbd"),
        ("color", "default color"),
        ("color_paused", "color if SABnzbd is paused"),
        ("color_downloading", "color if downloading"),
    )

    on_leftclick = "pause_resume"

    def init(self):
        """Initialize the URL used to connect to SABnzbd."""
        self.url = self.url.format(host=self.host, port=self.port,
                                   api_key=self.api_key)

    def run(self):
        """Connect to SABnzbd and get the data."""
        queue = urlopen(self.url + "&mode=queue").read().decode("UTF-8")
        queue = json.loads(queue)["queue"]

        self.status = queue["status"]

        if (self.is_paused()):
            color = self.color_paused
        elif (self.is_downloading()):
            color = self.color_downloading
        else:
            color = self.color

        self.output = {
            "full_text": self.format.format(**queue) if (self.is_downloading())
            else self.format_paused.format(**queue),
            "color": color
        }

    def pause_resume(self):
        """Toggle between pausing or resuming downloading."""
        if (self.is_paused()):
            urlopen(self.url + "&mode=resume")
        else:
            urlopen(self.url + "&mode=pause")

    def is_paused(self):
        """Return True if downloads are currently paused."""
        return (self.status == "Paused")

    def is_downloading(self):
        """Return True if downloads are running."""
        return (self.status == "Downloading")
