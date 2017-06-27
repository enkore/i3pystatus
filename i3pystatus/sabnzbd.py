from i3pystatus import IntervalModule
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

import json
import webbrowser


class sabnzbd(IntervalModule):
    """
    Displays the current status of SABnzbd.

    A leftclick pauses/resumes downloading.
    A rightclick opens SABnzbd inside a browser.

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
    on_rightclick = "open_browser"

    def init(self):
        """Initialize the URL used to connect to SABnzbd."""
        self.url = self.url.format(host=self.host, port=self.port,
                                   api_key=self.api_key)

    def run(self):
        """Connect to SABnzbd and get the data."""
        try:
            answer = urlopen(self.url + "&mode=queue").read().decode()
        except (HTTPError, URLError) as error:
            self.output = {
                "full_text": str(error.reason),
                "color": "#FF0000"
            }
            return

        answer = json.loads(answer)

        # if answer["status"] exists and is False, an error occured
        if not answer.get("status", True):
            self.output = {
                "full_text": answer["error"],
                "color": "#FF0000"
            }
            return

        queue = answer["queue"]
        self.status = queue["status"]

        if self.is_paused():
            color = self.color_paused
        elif self.is_downloading():
            color = self.color_downloading
        else:
            color = self.color

        if self.is_downloading():
            full_text = self.format.format(**queue)
        else:
            full_text = self.format_paused.format(**queue)

        self.output = {
            "full_text": full_text,
            "color": color
        }

    def pause_resume(self):
        """Toggle between pausing or resuming downloading."""
        if self.is_paused():
            urlopen(self.url + "&mode=resume")
        else:
            urlopen(self.url + "&mode=pause")

    def is_paused(self):
        """Return True if downloads are currently paused."""
        return self.status == "Paused"

    def is_downloading(self):
        """Return True if downloads are running."""
        return self.status == "Downloading"

    def open_browser(self):
        """Open the URL of SABnzbd inside a browser."""
        webbrowser.open(
            "http://{host}:{port}/".format(host=self.host, port=self.port))
