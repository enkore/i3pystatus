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

        cdict = {"core{}".format(key): str(value) for key, value in enumerate(mhz_values)}
        cdict['avg'] = str(sum(mhz_values) / len(mhz_values))

        self.output = {
            "full_text": self.format.format(**cdict),
        }
