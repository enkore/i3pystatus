
import os

from i3pystatus import uname


def test_uname():
    KEYS = ("sysname", "nodename", "release", "version", "machine")

    uref = os.uname()

    for key in KEYS:
        um = uname.Uname(format="{" + key + "}")
        um.init()
        assert um.output["full_text"] == getattr(uref, key)
