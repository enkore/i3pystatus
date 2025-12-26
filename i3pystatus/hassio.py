from i3pystatus import IntervalModule
from requests import get, post
import json
import subprocess
import time


# Global cache for sharing state data between multiple Hassio instances
_hassio_cache = {}
_hassio_cache_time = {}


class Hassio(IntervalModule):
    """
    Displays the state of a Homeassistant.io entity
    Requires the PyPI package `requests`

    Left click toggles the entity state (for switches, lights, etc.)
    Middle click forces a refresh of the current state.
    Right click opens the Home Assistant dashboard in a browser.

    For monitoring multiple entities efficiently, see :py:mod:`hassio_multi`.

    .. rubric:: Available formatters

    * ``{friendly_name}`` — friendly name of the entity
    * ``{entity_id}`` — entity ID
    * ``{state}`` — current state
    * ``{last_change}`` — last state change time
    * ``{last_update}`` — last update time
    * Any entity attribute (e.g., ``{current_temperature}``, ``{brightness}``)

    .. rubric:: Example with entity attributes

    ::

        # Display thermostat current temperature
        status.register("hassio",
            entity_id="climate.garage_thermostat_2",
            hassio_url="http://homeassistant.local:8123",
            hassio_token="your_token",
            format="Garage: {current_temperature}°F",
        )
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
        "format",
        ("hide_state", "State value used to determine if the results should be hidden"),
        ("browser_cmd", "Command to open browser (default: xdg-open)"),
        ("use_cache", "Share state cache with other Hassio instances (reduces API calls)"),
        ("cache_timeout", "How long to use cached data in seconds (default: same as interval)"),
    )
    required = ("hassio_url", "hassio_token", "entity_id")
    desired_state = "on"
    good_color = "#00FF00"     # green
    bad_color = "#FF0000"      # red
    interval = 15
    hide_state = None
    format = "{friendly_name}: {state}"
    browser_cmd = "xdg-open"
    use_cache = False
    cache_timeout = None

    on_leftclick = "toggle"
    on_middleclick = "refresh"
    on_rightclick = "open_dashboard"

    def _get_headers(self):
        return {
            "content-type": "application/json",
            "Authorization": "Bearer %s" % self.hassio_token
        }

    def _fetch_entity(self, entity_id):
        """Fetch a single entity state, optionally using cache"""
        cache_key = (self.hassio_url, self.hassio_token)
        cache_timeout = self.cache_timeout if self.cache_timeout else self.interval

        if self.use_cache:
            # Check if we have fresh cached data
            if cache_key in _hassio_cache:
                cache_age = time.time() - _hassio_cache_time.get(cache_key, 0)
                if cache_age < cache_timeout:
                    # Use cached data
                    for entity in _hassio_cache[cache_key]:
                        if entity['entity_id'] == entity_id:
                            return entity
                    return None

            # Fetch all states and cache them
            url = "%s/api/states" % self.hassio_url
            response = get(url, headers=self._get_headers())
            all_states = json.loads(response.text)
            _hassio_cache[cache_key] = all_states
            _hassio_cache_time[cache_key] = time.time()

            for entity in all_states:
                if entity['entity_id'] == entity_id:
                    return entity
            return None
        else:
            # Direct fetch for single entity
            url = "%s/api/states/%s" % (self.hassio_url, entity_id)
            response = get(url, headers=self._get_headers())
            return json.loads(response.text)

    def run(self):
        entity = self._fetch_entity(self.entity_id)

        if not entity:
            self.output = {
                "full_text": "Entity not found: %s" % self.entity_id,
                "color": self.bad_color
            }
            return

        # Start with all entity attributes
        cdict = dict(entity.get('attributes', {}))

        # Add/override with standard fields
        cdict.update({
            "friendly_name": entity['attributes'].get('friendly_name') or self.entity_id,
            "entity_id": entity['entity_id'] or self.entity_id,
            "last_change": entity.get('last_changed') or None,
            "last_update": entity.get('last_updated') or None,
            "state": entity['state']
        })

        color = self.good_color if entity['state'] == self.desired_state else self.bad_color
        if entity['state'] == self.hide_state:
            self.output = {"full_text": ''}
        else:
            self.output = {
                "full_text": self.format.format(**cdict),
                "color": color
            }

    def toggle(self):
        """Toggle the entity state (for switches, lights, input_booleans, etc.)"""
        domain = self.entity_id.split('.')[0]
        url = "%s/api/services/%s/toggle" % (self.hassio_url, domain)
        post(url, headers=self._get_headers(), json={"entity_id": self.entity_id})

    def refresh(self):
        """Force a refresh of the current state"""
        # Invalidate cache for this server
        cache_key = (self.hassio_url, self.hassio_token)
        if cache_key in _hassio_cache_time:
            _hassio_cache_time[cache_key] = 0
        self.run()

    def open_dashboard(self):
        """Open the Home Assistant dashboard in a browser"""
        subprocess.Popen(
            [self.browser_cmd, self.hassio_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
