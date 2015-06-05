from i3pystatus import IntervalModule


class CpuFreq(IntervalModule):
    format = "{avg}"
    settings = (
        "format",
        ("color", "The text color"),
        ("average", "Show average for every core"),
        ("file", "override default path"),
    )

    file = '/proc/cpuinfo'
    color = '#FFFFFF'

    def run(self):
        with open(self.file) as f:
            mhz_values = [float(line.split(':')[1]) for line in f if line.startswith('cpu MHz')]
            ghz_values = [value / 1000.0 for value in mhz_values]

        mhz = {"core{}".format(key): "{0:4.3f}".format(value) for key, value in enumerate(mhz_values)}
        ghz = {"core{}g".format(key): "{0:1.2f}".format(value) for key, value in enumerate(ghz_values)}
        cdict = mhz.copy()
        cdict.update(ghz)
        cdict['avg'] = "{0:4.3f}".format(sum(mhz_values) / len(mhz_values))
        cdict['avgg'] = "{0:1.2f}".format(sum(ghz_values) / len(ghz_values), 2)

        self.output = {
            "full_text": self.format.format(**cdict),
        }
