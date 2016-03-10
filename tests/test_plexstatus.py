"""
Basic test for the plexstatus module
"""

import unittest
from mock import patch
from unittest.mock import MagicMock
from urllib.request import urlopen
from i3pystatus import plexstatus


class PlexstatusTest(unittest.TestCase):

    @patch('i3pystatus.plexstatus.urlopen', autospec=True)
    def test_not_stream(self, urlopen):
        """
        Test output when nothing is being streamed
        """
        null_stream = b'<?xml version="1.0" encoding="UTF-8"?>\n<MediaContainer size="0">\n</MediaContainer>'
        plexstatus.urlopen.return_value.read.return_value = null_stream
        plxstat = plexstatus.Plexstatus(apikey='111111', address='127.0.0.1')
        plxstat.run()
        self.assertTrue(plxstat.output == {})

    @patch('i3pystatus.plexstatus.urlopen', autospec=True)
    def test_streaming(self, urlopen):
        """
        Test output from side-loaded xml (generated from a real plex server
        response)
        """
        streamfile = open('plexstatus.xml', 'rb')
        stream = streamfile.read()
        streamfile.close()
        plexstatus.urlopen.return_value.read.return_value = stream
        plxstat = plexstatus.Plexstatus(apikey='111111', address='127.0.0.1')
        plxstat.run()
        self.assertTrue(plxstat.output['full_text'] == 'Chrome: Big Buck Bunny')


if __name__ == '__main__':
    unittest.main()
