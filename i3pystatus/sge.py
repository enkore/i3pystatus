import subprocess

from lxml import etree

from i3pystatus import IntervalModule


class SGETracker(IntervalModule):
    """
    Used to display status of Batch computing jobs on a cluster running Sun Grid Engine.
    The data is collected via ssh, so a valid ssh address must be specified.

    Requires lxml.
    """

    interval = 60

    settings = (
        ("ssh", "The SSH connection address. Can be user@host or user:password@host or user@host -p PORT etc."),
        'color', 'format'
    )
    required = ("ssh",)

    format = "SGE qw: {queued} / r: {running} / Eqw: {error}"
    on_leftclick = None
    color = "#ffffff"

    def parse_qstat_xml(self):
        xml = subprocess.check_output("ssh {0} \"qstat -xml\"".format(self.ssh),
                                      stderr=subprocess.STDOUT,
                                      shell=True)
        root = etree.fromstring(xml)
        job_dict = {'qw': 0, 'Eqw': 0, 'r': 0}

        for j in root.xpath('//job_info/job_info/job_list'):
            job_dict[j.find("state").text] += 1

        for j in root.xpath('//job_info/queue_info/job_list'):
            job_dict[j.find("state").text] += 1

        return job_dict

    def run(self):
        jobs = self.parse_qstat_xml()

        fdict = {
            "queued": jobs['qw'],
            "error": jobs['Eqw'],
            "running": jobs['r']
        }

        self.data = fdict
        self.output = {
            "full_text": self.format.format(**fdict).strip(),
            "color": self.color
        }
