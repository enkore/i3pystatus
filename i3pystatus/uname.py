import os

from i3pystatus import Module


class Uname(Module):
    """
    uname(1) like module.

    .. rubric:: Available formatters

    * `{sysname}` — operating system name
    * `{nodename}` — name of machine on network (implementation-defined)
    * `{release}` — operating system release
    * `{version}` — operating system version
    * `{machine}` — hardware identifier
    """

    format = "{sysname} {release}"
    settings = (
        ("format", "format string used for output"),
    )

    def init(self):
        uname_result = os.uname()
        fdict = {
            "sysname": uname_result.sysname,
            "nodename": uname_result.nodename,
            "release": uname_result.release,
            "version": uname_result.version,
            "machine": uname_result.machine,
        }
        self.data = fdict
        self.output = {
            "full_text": self.format.format(**fdict),
        }
