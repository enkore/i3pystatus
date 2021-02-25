"""
Basic test for the hassio module
"""

import unittest
from mock import patch
from unittest.mock import MagicMock
from requests import get
from i3pystatus import hassio
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


if __name__ == '__main__':
    unittest.main()
