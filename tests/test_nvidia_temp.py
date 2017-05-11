"""
Basic test for the nvidia_temp module
"""

import subprocess
import unittest
from unittest.mock import MagicMock
from i3pystatus import nvidia_temp


class TestNvidiaTemperature(unittest.TestCase):

    def test_nvidia_temp(self):
        """
        Test the return of nvidia_temp module
        """
        cases = ('57', '41', '47')
        for temperature in cases:
            subprocess.getoutput = MagicMock(return_value=temperature)
            nvt = nvidia_temp.NvidiaTemperature()
            nvt.run()
            self.assertTrue(nvt.output['full_text'] == '%s °C' % temperature)


if __name__ == '__main__':
    unittest.main()
