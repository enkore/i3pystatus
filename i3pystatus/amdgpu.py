import os

from i3pystatus import IntervalModule


class Amdgpu(IntervalModule):
    """
    Shows information about gpu's using the amdgpu driver

    .. rubric :: Available formatters

    * `{temp}`
    * `{sclk}`  - Gpu clock speed
    * `{mclk}`  - Memory clock speed
    """

    settings = (
        'format',
        ('card', '[1, 2, ...] card to read (options are in /sys/class/drm/)')
    )

    card = 0
    format = '{temp} {mclk} {sclk}'

    def init(self):
        self.dev_path = '/sys/class/drm/card{}/device/'.format(self.card)
        self.detect_hwmon()

    def detect_hwmon(self):
        hwmon_base = self.dev_path + 'hwmon/'
        self.hwmmon_path = hwmon_base + os.listdir(hwmon_base)[0] + '/'

    def run(self):
        self.data = dict(
            sclk=self.get_sclk(),
            mclk=self.get_mclk(),
            temp=self.get_temp()
        )

        self.output = {
            'full_text': self.format.format(**self.data)
        }

    @staticmethod
    def parse_clk_reading(reading):
        for l in reading.splitlines():
            if l.endswith('*'):
                return l.split(' ')[1]

    def get_mclk(self):
        with open(self.dev_path + 'pp_dpm_mclk') as f:
            return self.parse_clk_reading(f.read())

    def get_sclk(self):
        with open(self.dev_path + 'pp_dpm_sclk') as f:
            return self.parse_clk_reading(f.read())

    def get_temp(self):
        with open(self.hwmmon_path + 'temp1_input') as f:
            return float(f.read()) / 1000
