import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import webbrowser
import json

from i3pystatus import IntervalModule


class pyLoad(IntervalModule):
    """
    Shows pyLoad status

    .. rubric:: Available formatters

    * `{captcha}` — see captcha_true and captcha_false, which are the values filled in for this formatter
    * `{progress}` — average over all running downloads
    * `{progress_all}` — percentage of completed files/links in queue
    * `{speed}` — kilobytes/s
    * `{download}` — downloads enabled, also see download_true and download_false
    * `{total}` — number of downloads
    * `{free_space}` — free space in download directory in gigabytes
    """
    interval = 5

    settings = (
        ("address", "Address of pyLoad webinterface"),
        "format",
        "captcha_true", "captcha_false",
        "download_true", "download_false",
        "username", "password",
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
    )
    required = ("username", "password")
    keyring_backend = None

    address = "http://127.0.0.1:8000"
    format = "{captcha} {progress_all:.1f}% {speed:.1f} kb/s"
    captcha_true = "Captcha waiting"
    captcha_false = ""
    download_true = "Downloads enabled"
    download_false = "Downloads disabled"
    on_leftclick = "open_webbrowser"

    def _rpc_call(self, method, data=None):
        if not data:
            data = {}
        urlencoded = urllib.parse.urlencode(data).encode("ascii")
        return json.loads(self.opener.open("{address}/api/{method}/".format(address=self.address, method=method),
                                           urlencoded).read().decode("utf-8"))

    def init(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj))

    def login(self):
        return self._rpc_call("login", {
            "username": self.username,
            "password": self.password,
        })

    def run(self):
        self.login()
        server_status = self._rpc_call("statusServer")
        downloads_status = self._rpc_call("statusDownloads")

        if downloads_status:
            progress = sum(dl["percent"]
                           for dl in downloads_status) / len(downloads_status) * 100
        else:
            progress = 100.0

        fdict = {
            "download": self.download_true if server_status["download"] else self.download_false,
            "speed": server_status["speed"] / 1024,
            "progress": progress,
            "progress_all": sum(pkg["linksdone"] for pkg in self._rpc_call("getQueue")) / server_status["total"] * 100,
            "captcha": self.captcha_true if self._rpc_call("isCaptchaWaiting") else self.captcha_false,
            "free_space": self._rpc_call("freeSpace") / (1024 ** 3),
        }

        self.data = fdict
        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "instance": self.address,
        }

    def open_webbrowser(self):
        webbrowser.open_new_tab(self.address)
