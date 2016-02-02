from i3pystatus import Status, IntervalModule
from i3pystatus.core.util import internet, require, user_open
import vk


class Vk(IntervalModule):
    """
    Display amount of unread messages in VK social network.
    Creating your own VK API app is highly recommended for your own privacy, though there is a default one provided.
    Reference vk.com/dev for instructions on creating VK API app.
    If access_token is not specified, the module will try to open a request page in browser.
    You will need to manually copy obtained acess token to your config file.
    Requires the PyPI package `vk`.
    """

    API_LINK = "https://oauth.vk.com/authorize?client_id={id}&display=page&revoke=1&scope=messages,offline&response_type=token&v=5.40"
    app_id = 5160484
    access_token = None
    session = None
    token_error = "Vk: token error"
    format = '{unread}/{total}'
    interval = 1
    color = "#ffffff"
    color_unread = "#ffffff"
    color_bad = "#ff0000"

    settings = (
        ("app_id", "Id of your VK API app"),
        ("access_token", "Your access token. You must have `messages` and `offline` access permissions"),
        ("token_error", "Message to be shown if there's some problem with your token"),
        ("color", "General color of the output"),
        ("color_bad", "Color of the output in case of access token error"),
        ("color_unread", "Color of the output if there are unread messages"),
    )

    @require(internet)
    def token_request(self, func):
        user_open(self.API_LINK.format(id=self.app_id))
        self.run = func

    @require(internet)
    def init(self):
        if self.access_token:
            self.session = vk.AuthSession(app_id=self.app_id, access_token=self.access_token)
            self.api = vk.API(self.session, v='5.40', lang='en', timeout=10)
            try:
                permissions = int(self.api.account.getAppPermissions())
                assert((permissions & 65536 == 65536) and (permissions & 4096 == 4096))
            except:
                self.token_request(self.error)
        else:
            self.token_request(lambda: None)

    @require(internet)
    def run(self):
        total = self.api.messages.getDialogs()['count']
        unread = self.api.messages.getDialogs(unread=1)['count']

        if unread > 0:
            color = self.color_unread
        else:
            color = self.color

        self.output = {
            "full_text": self.format.format(
                total=total,
                unread=unread
            ),
            "color": color
        }

    def error(self):
        self.output = {"full_text": self.token_error,
                       "color": self.color_bad}
