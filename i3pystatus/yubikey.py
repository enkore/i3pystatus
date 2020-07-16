import re
import os
import time

from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell


class Yubikey(IntervalModule):
    """
    This module allows you to lock and unlock your Yubikey in order to avoid
    the OTP to be triggered accidentally.

    @author Daniel Theodoro <daniel.theodoro AT gmail.com>
    """

    interval = 1
    format = "Yubikey: 🔒"
    unlocked_format = "Yubikey: 🔓"
    timeout = 5
    color = "#00FF00"
    unlock_color = "#FF0000"

    settings = (
        ("format", "Format string"),
        ("unlocked_format", "Format string when the key is unlocked"),
        ("timeout", "How long the Yubikey will be unlocked (default: 5)"),
        ("color", "Standard color"),
        ("unlock_color", "Set the color used when the Yubikey is unlocked"),
    )

    on_leftclick = ["set_lock", True]

    find_regex = re.compile(
        r".*yubikey.*id=(?P<yubid>\d+).*$",
        re.IGNORECASE
    )

    status_regex = re.compile(
        r".*device enabled.*(?P<status>\d)$",
        re.IGNORECASE
    )

    lock_file = f"/var/tmp/Yubikey-{os.geteuid()}.lock"

    def __init__(self):
        super().__init__()

    @property
    def _device_id(self):
        command = run_through_shell(
            "xinput list",
            enable_shell=True
        )

        rval = ""

        if command.rc == 0:
            for line in command.out.splitlines():
                match = self.find_regex.match(line)
                if match:
                    rval = match.groupdict().get("yubid", "")
                    break

        return rval

    def device_status(self):

        rval = "notfound"

        if not self._device_id:
            return rval

        result = run_through_shell(
            f"xinput list-props {self._device_id}",
            enable_shell=True
        )
        if result.rc == 0:
            match = self.status_regex.match(result.out.splitlines()[1])
            if match and "status" in match.groupdict():
                status = int(match.groupdict()["status"])
                if status:
                    rval = "unlocked"
                else:
                    rval = "locked"

        return rval

    def _check_lock(self):
        try:
            st = os.stat(self.lock_file)

            if int(time.time() - st.st_ctime) > self.timeout:
                self.set_lock()

        except IOError:
            self.set_lock()

    def set_lock(self, unlock=False):

        if unlock:
            command = "enable"
        else:
            command = "disable"

        run_through_shell(f"xinput {command} {self._device_id}")
        open(self.lock_file, mode="w").close()

    def _clear_lock(self):
        try:
            os.unlink(self.lock_file)
        except FileNotFoundError:
            pass

    def run(self):
        status = self.device_status()

        if status == "notfound":
            self._clear_lock()
            self.output = {
                "full_text": "",
            }
        else:
            if status == "unlocked":
                self.output = {
                    "full_text": self.unlocked_format,
                    "color": self.unlock_color
                }
                self._check_lock()

            elif status == "locked":
                self.output = {
                    "full_text": self.format,
                    "color": self.color
                }
            else:
                self.output = {
                    "full_text": f"Error: {status}",
                }
