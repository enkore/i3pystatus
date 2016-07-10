"""
Basic test for the openfiles module
"""

import unittest
from tempfile import TemporaryDirectory
from shutil import copyfile
from i3pystatus import openfiles


class OpenfilesTest(unittest.TestCase):

    def test_openfiles(self):
        """
        Test output of open files
        """
        # copy file-nr so we have a known/unchanged source file
        with TemporaryDirectory() as tmpdirname:
            copyfile('/proc/sys/fs/file-nr', tmpdirname + '/file-nr')
            cur_filenr = open(tmpdirname + '/file-nr', 'r')
            openfilehandles, ununsed, maxfiles = cur_filenr.readlines()[0].split()
            cur_filenr.close()
            i3openfiles = openfiles.Openfiles(filenr_path=tmpdirname + '/file-nr')
            i3openfiles.run()
            self.assertTrue(i3openfiles.output['full_text'] == 'open/max: %s/%s' % (openfilehandles, maxfiles))


if __name__ == '__main__':
    unittest.main()
