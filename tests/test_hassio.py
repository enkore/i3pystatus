"""
Basic test for the hassio module
"""

import unittest
from mock import patch
from requests import get
from i3pystatus import hassio
from i3pystatus import hassio_multi
import json

# inline json of hassio api response
STREAM = {'attributes': {'friendly_name': 'Light',
                         'node_id': 18,
                         'supported_features': 1,
                         'value_id': '72054591347734729',
                         'value_index': 0,
                         'value_instance': 1},
          'context': {'id': '54188133d21271036bbfb089019a3481',
                      'parent_id': None,
                      'user_id': None},
          'entity_id': 'asdf1234',
          'last_changed': '2021-02-24T23:37:25.627676+00:00',
          'last_updated': '2021-02-24T23:37:25.627676+00:00',
          'state': 'off'}

HASSIO_URL = 'http://localhost:8123'
FAKETOKEN = 'ihasatoken'


class HassioTest(unittest.TestCase):

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_not_desired_state(self, get):
        """
        Test output when state matches desired state
        """
        hassio.get.return_value.text = json.dumps(STREAM)
        hassiostat = hassio.Hassio(entity_id='asdf1234',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN,
                                   good_color="#00FF00",
                                   bad_color="#FF0000",
                                   desired_state='on')
        hassiostat.run()
        import pdb
        self.assertTrue(hassiostat.output == {'full_text': 'Light: off', 'color': '#FF0000'})

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_desired_state(self, urlopen):
        """
        Test output from side-loaded xml (generated from a real hassio server
        response)
        """
        hassio.get.return_value.text = json.dumps(STREAM)
        hassiostat = hassio.Hassio(entity_id='asdf1234',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN,
                                   good_color="#00FF00",
                                   bad_color="#FF0000",
                                   desired_state='off')
        hassiostat.run()
        self.assertTrue(hassiostat.output == {'full_text': 'Light: off', 'color': '#00FF00'})


# Multiple entities for HassioMulti tests
MULTI_STREAM = [
    {'attributes': {'friendly_name': 'Living Room Light'},
     'entity_id': 'light.living_room',
     'last_changed': '2021-02-24T23:37:25.627676+00:00',
     'last_updated': '2021-02-24T23:37:25.627676+00:00',
     'state': 'on'},
    {'attributes': {'friendly_name': 'Kitchen Light'},
     'entity_id': 'light.kitchen',
     'last_changed': '2021-02-24T23:37:25.627676+00:00',
     'last_updated': '2021-02-24T23:37:25.627676+00:00',
     'state': 'off'},
    {'attributes': {'friendly_name': 'Garage Door'},
     'entity_id': 'switch.garage_door',
     'last_changed': '2021-02-24T23:37:25.627676+00:00',
     'last_updated': '2021-02-24T23:37:25.627676+00:00',
     'state': 'off'},
]


class HassioMultiTest(unittest.TestCase):

    @patch('i3pystatus.hassio_multi.get', autospec=True)
    def test_multi_fetch_all_states(self, mock_get):
        """
        Test that HassioMulti fetches all states in one API call
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room', 'light.kitchen'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN
        )
        hassiomulti.run()

        # Verify only one API call was made (to /api/states)
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        self.assertEqual(call_url, '%s/api/states' % HASSIO_URL)

    @patch('i3pystatus.hassio_multi.get', autospec=True)
    def test_multi_displays_first_entity(self, mock_get):
        """
        Test that HassioMulti displays the first entity by default
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room', 'light.kitchen'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            format="{friendly_name}: {state}"
        )
        hassiomulti.run()

        self.assertIn('Living Room Light', hassiomulti.output['full_text'])
        self.assertIn('on', hassiomulti.output['full_text'])

    @patch('i3pystatus.hassio_multi.get', autospec=True)
    def test_multi_next_entity(self, mock_get):
        """
        Test cycling through entities with next_entity
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room', 'light.kitchen'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            format="{friendly_name}"
        )
        hassiomulti.run()

        # First entity
        self.assertIn('Living Room Light', hassiomulti.output['full_text'])

        # Cycle to next
        hassiomulti.next_entity()
        hassiomulti.run()
        self.assertIn('Kitchen Light', hassiomulti.output['full_text'])

        # Cycle wraps around
        hassiomulti.next_entity()
        hassiomulti.run()
        self.assertIn('Living Room Light', hassiomulti.output['full_text'])

    @patch('i3pystatus.hassio_multi.get', autospec=True)
    def test_multi_prev_entity(self, mock_get):
        """
        Test cycling backwards through entities
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room', 'light.kitchen'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            format="{friendly_name}"
        )
        hassiomulti.run()

        # Go backwards from first (wraps to last)
        hassiomulti.prev_entity()
        hassiomulti.run()
        self.assertIn('Kitchen Light', hassiomulti.output['full_text'])

    @patch('i3pystatus.hassio_multi.post', autospec=True)
    @patch('i3pystatus.hassio_multi.get', autospec=True)
    def test_multi_toggle_current_entity(self, mock_get, mock_post):
        """
        Test that toggle affects the currently displayed entity
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room', 'light.kitchen'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN
        )
        hassiomulti.run()

        # Toggle first entity
        hassiomulti.toggle()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json'], {'entity_id': 'light.living_room'})

        # Cycle to next and toggle
        hassiomulti.next_entity()
        hassiomulti.run()
        hassiomulti.toggle()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json'], {'entity_id': 'light.kitchen'})

    @patch('i3pystatus.hassio_multi.get', autospec=True)
    def test_multi_entity_count_formatter(self, mock_get):
        """
        Test entity_index and entity_count formatters
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room', 'light.kitchen', 'switch.garage_door'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            format="[{entity_index}/{entity_count}] {friendly_name}"
        )
        hassiomulti.run()

        self.assertIn('[1/3]', hassiomulti.output['full_text'])

        hassiomulti.next_entity()
        hassiomulti.run()
        self.assertIn('[2/3]', hassiomulti.output['full_text'])

    def test_multi_default_click_handlers(self):
        """
        Test that HassioMulti has correct default click handlers
        """
        hassiomulti = hassio_multi.HassioMulti(
            entity_ids=['light.living_room'],
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN
        )
        self.assertEqual(hassiomulti.on_leftclick, 'next_entity')
        self.assertEqual(hassiomulti.on_rightclick, 'toggle')
        self.assertEqual(hassiomulti.on_middleclick, 'refresh')
        self.assertEqual(hassiomulti.on_upscroll, 'prev_entity')
        self.assertEqual(hassiomulti.on_downscroll, 'next_entity')


class HassioCacheTest(unittest.TestCase):

    def setUp(self):
        # Clear the global cache before each test
        hassio._hassio_cache.clear()
        hassio._hassio_cache_time.clear()

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_cache_reduces_api_calls(self, mock_get):
        """
        Test that enabling cache reduces API calls for multiple instances
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)

        # Create two instances with caching enabled
        hassio1 = hassio.Hassio(
            entity_id='light.living_room',
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            use_cache=True,
            cache_timeout=60
        )
        hassio2 = hassio.Hassio(
            entity_id='light.kitchen',
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            use_cache=True,
            cache_timeout=60
        )

        # First instance makes the API call
        hassio1.run()
        self.assertEqual(mock_get.call_count, 1)

        # Second instance uses the cache
        hassio2.run()
        self.assertEqual(mock_get.call_count, 1)  # Still 1, no new call

        # Both should have valid output
        self.assertIn('Living Room Light', hassio1.output['full_text'])
        self.assertIn('Kitchen Light', hassio2.output['full_text'])

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_cache_fetches_all_states(self, mock_get):
        """
        Test that cache mode fetches from /api/states (all entities)
        """
        mock_get.return_value.text = json.dumps(MULTI_STREAM)

        hassiostat = hassio.Hassio(
            entity_id='light.living_room',
            hassio_url=HASSIO_URL,
            hassio_token=FAKETOKEN,
            use_cache=True
        )
        hassiostat.run()

        # Should call /api/states, not /api/states/<entity_id>
        call_url = mock_get.call_args[0][0]
        self.assertEqual(call_url, '%s/api/states' % HASSIO_URL)


if __name__ == '__main__':
    unittest.main()
