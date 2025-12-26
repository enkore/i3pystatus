from i3pystatus import IntervalModule
from requests import get, post
import json
import subprocess


class HassioMulti(IntervalModule):
    """
    Displays multiple Homeassistant.io entities with a single API call.
    Requires the PyPI package `requests`

    This is more efficient than multiple Hassio instances when monitoring
    several entities, as it fetches all states in one bulk API call.

    Left click cycles to the next entity.
    Right click toggles the current entity.
    Middle click refreshes all entities.
    Scroll up/down cycles through entities.

    .. rubric:: Available formatters

    * ``{friendly_name}`` — friendly name of current entity
    * ``{entity_id}`` — entity ID
    * ``{state}`` — current state
    * ``{last_change}`` — last state change time
    * ``{last_update}`` — last update time
    * ``{entity_index}`` — current entity index (1-based)
    * ``{entity_count}`` — total number of entities
    * Any entity attribute (e.g., ``{current_temperature}``, ``{brightness}``)

    .. rubric:: Example usage

    ::

        status.register("hassio_multi",
            entity_ids=["light.living_room", "switch.fan", "sensor.temperature"],
            hassio_url="http://homeassistant.local:8123",
            hassio_token="your_token_here",
            format="{friendly_name}: {state} [{entity_index}/{entity_count}]",
        )
    """

    settings = (
        ("entity_ids", "List of entity IDs to track."),
        ("hassio_url", "URL to your hassio install."),
        ("hassio_token", "HomeAssistant API token."),
        ("interval", "Update interval."),
        ("desired_state", "The desired or \"good\" state of entities."),
        ("good_color", "Color of text while entity is in desired state"),
        ("bad_color", "Color of text while entity is not in desired state"),
        "format",
        ("hide_state", "State value used to hide an entity from display"),
        ("browser_cmd", "Command to open browser (default: xdg-open)"),
    )
    required = ("hassio_url", "hassio_token", "entity_ids")
    desired_state = "on"
    good_color = "#00FF00"
    bad_color = "#FF0000"
    interval = 15
    hide_state = None
    format = "{friendly_name}: {state}"
    browser_cmd = "xdg-open"

    on_leftclick = "next_entity"
    on_rightclick = "toggle"
    on_middleclick = "refresh"
    on_upscroll = "prev_entity"
    on_downscroll = "next_entity"

    _entity_index = 0
    _entities_data = []

    def _get_headers(self):
        return {
            "content-type": "application/json",
            "Authorization": "Bearer %s" % self.hassio_token
        }

    def _fetch_all_states(self):
        """Fetch all entity states in one API call"""
        url = "%s/api/states" % self.hassio_url
        response = get(url, headers=self._get_headers())
        all_states = json.loads(response.text)

        # Filter to only the entities we care about
        entity_map = {e['entity_id']: e for e in all_states}
        result = []
        for eid in self.entity_ids:
            if eid in entity_map:
                result.append(entity_map[eid])
        return result

    def run(self):
        self._entities_data = self._fetch_all_states()

        if not self._entities_data:
            self.output = {
                "full_text": "No entities found",
                "color": self.bad_color
            }
            return

        # Filter out hidden entities for display
        visible_entities = [
            e for e in self._entities_data
            if e['state'] != self.hide_state
        ]

        if not visible_entities:
            self.output = {"full_text": ''}
            return

        # Ensure index is valid
        self._entity_index = self._entity_index % len(visible_entities)
        entity = visible_entities[self._entity_index]

        # Start with all entity attributes
        cdict = dict(entity.get('attributes', {}))

        # Add/override with standard fields
        cdict.update({
            "friendly_name": entity['attributes'].get('friendly_name') or entity['entity_id'],
            "entity_id": entity['entity_id'],
            "last_change": entity.get('last_changed') or None,
            "last_update": entity.get('last_updated') or None,
            "state": entity['state'],
            "entity_index": self._entity_index + 1,
            "entity_count": len(visible_entities),
        })

        color = self.good_color if entity['state'] == self.desired_state else self.bad_color
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": color
        }

    def _get_current_entity_id(self):
        """Get the entity_id of the currently displayed entity"""
        visible = [e for e in self._entities_data if e['state'] != self.hide_state]
        if visible and self._entity_index < len(visible):
            return visible[self._entity_index]['entity_id']
        return None

    def next_entity(self):
        """Cycle to next entity"""
        visible = [e for e in self._entities_data if e['state'] != self.hide_state]
        if visible:
            self._entity_index = (self._entity_index + 1) % len(visible)

    def prev_entity(self):
        """Cycle to previous entity"""
        visible = [e for e in self._entities_data if e['state'] != self.hide_state]
        if visible:
            self._entity_index = (self._entity_index - 1) % len(visible)

    def toggle(self):
        """Toggle the current entity state"""
        entity_id = self._get_current_entity_id()
        if entity_id:
            domain = entity_id.split('.')[0]
            url = "%s/api/services/%s/toggle" % (self.hassio_url, domain)
            post(url, headers=self._get_headers(), json={"entity_id": entity_id})

    def refresh(self):
        """Force refresh all entities"""
        self.run()

    def open_dashboard(self):
        """Open the Home Assistant dashboard in a browser"""
        subprocess.Popen(
            [self.browser_cmd, self.hassio_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

