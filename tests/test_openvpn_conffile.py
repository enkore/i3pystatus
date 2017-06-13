"""
Basic test for the openvpn conffile backend
"""

import unittest
from i3pystatus import openvpn
from i3pystatus.openvpn import conffile


class OpenvpnConffileTest(unittest.TestCase):

    def test_openvpnconffile_up(self):
        """
        Test status output of openvpn being "up"
        """

        ovpnconffile = openvpn.Openvpn(vpn_name='testvpn', status_up='up', backend=conffile.File(conf_file='tests/ovpn_up.conf'))
        ovpnconffile.run()
        self.assertTrue(ovpnconffile.output['full_text'] == 'testvpn up')

    def test_openvpnconffile_down(self):
        """
        Test status output of openvpn being "down"
        """

        ovpnconffile = openvpn.Openvpn(vpn_name='testvpn', status_down='down', backend=conffile.File(conf_file='tests/ovpn_down.conf'))
        ovpnconffile.run()
        self.assertTrue(ovpnconffile.output['full_text'] == 'testvpn down')


if __name__ == '__main__':
    unittest.main()
