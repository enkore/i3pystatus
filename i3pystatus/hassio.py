from i3pystatus import IntervalModule
from requests import get
import json


class Hassio(IntervalModule):
    """
    Displays the state of a Homeassistant.io entity
    Requires the PyPI package `requests`
    """

    settings = (
        ("entity_id", "Entity ID to track."),
        ("hassio_url", "URL to your hassio install. (default: "
            "https://localhost:8123)"),
        ("hassio_token", "HomeAssistant API token "
            "(https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token)"),
        ("interval", "Update interval."),
        ("desired_state", "The desired or \"good\" state of the entity."),
        ("good_color", "Color of text while entity is in desired state"),
        ("bad_color", "Color of text while entity is not in desired state"),
        "format"
    )
    required = ("hassio_url", "hassio_token", "entity_id")
    desired_state = "on"
    good_color = "#00FF00"     # green
    bad_color = "#FF0000"      # red
    interval = 15
    format = "{friendly_name}: {state}"

    def run(self):
        headers = {"content-type": "application/json",
                   "Authorization": "Bearer %s" % self.hassio_token}
        url = "%s/api/states/%s" % (self.hassio_url, self.entity_id)
        response = get(url, headers=headers)
        entity = json.loads(response.text)

        cdict = {
            "friendly_name": entity['attributes']['friendly_name'] or None,
            "entity_id": entity['entity_id'] or self.entity_id,
            "last_change": entity['last_changed'] or None,
            "last_update": entity['last_updated'] or None,
            "state": entity['state']
        }

        color = self.good_color if entity['state'] == self.desired_state else self.bad_color
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }
