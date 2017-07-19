"""
Basic test for the openvpn conffile backend
"""

import unittest
from mock import patch
from i3pystatus import openvpn
from i3pystatus.openvpn import conffile


class OpenvpnConffileTest(unittest.TestCase):

    @patch('i3pystatus.openvpn.conffile.os')
    def test_openvpnconffile_up(self, os):
        """
        Test status output of openvpn being "up"
        """

        os.listdir.return_value = ['1', '11', '2', '22', '3', '33']
        ovpnconffile = openvpn.Openvpn(vpn_name='testvpn', status_up='up', backend=conffile.File(conf_file='tests/ovpn.conf'))
        ovpnconffile.run()
        self.assertTrue(ovpnconffile.output['full_text'] == 'testvpn up')

    @patch('i3pystatus.openvpn.conffile.os')
    def test_openvpnconffile_down(self, os):
        """
        Test status output of openvpn being "down"
        """

        os.listdir.return_value = ['11', '2', '22', '3', '33']
        ovpnconffile = openvpn.Openvpn(vpn_name='testvpn', status_down='down', backend=conffile.File(conf_file='tests/ovpn.conf'))
        ovpnconffile.run()
        self.assertTrue(ovpnconffile.output['full_text'] == 'testvpn down')


if __name__ == '__main__':
    unittest.main()
