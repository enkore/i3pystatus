"""
The module gathers information by default from `/proc/cpuinfo` about the current cpu frequency
"""
# coding=utf-8
from i3pystatus import IntervalModule


class CpuFreq(IntervalModule):
    """
    class uses by default `/proc/cpuinfo` to determine the current cpu frequency

    .. rubric:: Available formatters

    * `{avg}` - mean from all cores in MHz `4.3f`
    * `{avgg}` - mean from all cores in GHz `1.2f`
    * `{corex}` - frequency of a selected core in MHz `4.3f`
    * `{corexg}` - frequesncy of a selscted core in GHz `1.2f`

    """
    format = "{avgg}"
    settings = (
        "format",
        ("color", "The text color"),
        ("file", "override default path"),
    )

    file = '/proc/cpuinfo'
    color = '#FFFFFF'

    def createvaluesdict(self):
        """
        function processes the /proc/cpuinfo file
        :return: dictionary used as the full-text output for the module
        """
        with open(self.file) as f:
            mhz_values = [float(line.split(':')[1]) for line in f if line.startswith('cpu MHz')]
            ghz_values = [value / 1000.0 for value in mhz_values]

        mhz = {"core{}".format(key): "{0:4.3f}".format(value) for key, value in enumerate(mhz_values)}
        ghz = {"core{}g".format(key): "{0:1.2f}".format(value) for key, value in enumerate(ghz_values)}
        cdict = mhz.copy()
        cdict.update(ghz)
        cdict['avg'] = "{0:4.3f}".format(sum(mhz_values) / len(mhz_values))
        cdict['avgg'] = "{0:1.2f}".format(sum(ghz_values) / len(ghz_values), 2)
        return cdict

    def run(self):
        cdict = self.createvaluesdict()

        self.output = {
            "full_text": self.format.format(**cdict),
            "color": self.color,
            "format": self.format,
        }
