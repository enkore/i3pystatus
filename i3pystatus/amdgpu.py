import os

from i3pystatus import IntervalModule


class Amdgpu(IntervalModule):
    """
    Shows information about gpu's using the amdgpu driver

    .. rubric :: Available formatters

    * `{temp}`
    * `{sclk}`      - Gpu clock speed
    * `{mclk}`      - Memory clock speed
    * `{fan_speed}` - Fan speed
    * `{gpu_usage}` - Gpu Usage percent
    """

    settings = (
        'format',
        'color',
        ('card', '[1, 2, ...] card to read (options are in /sys/class/drm/)')
    )

    card = 0
    color = None
    format = '{temp} {mclk} {sclk}'

    def init(self):
        self.info_gatherers = []
        self.dev_path = '/sys/class/drm/card{}/device/'.format(self.card)
        self.detect_hwmon()
        if 'sclk' in self.format:
            self.info_gatherers.append(self.get_sclk)

        if 'mclk' in self.format:
            self.info_gatherers.append(self.get_mclk)

        if 'temp' in self.format:
            self.info_gatherers.append(self.get_temp)

        if 'fan_speed' in self.format:
            self.info_gatherers.append(self.get_fan_speed)

        if 'gpu_usage' in self.format:
            self.info_gatherers.append(self.get_gpu_usage)

    def detect_hwmon(self):
        hwmon_base = self.dev_path + 'hwmon/'
        self.hwmon_path = hwmon_base + os.listdir(hwmon_base)[0] + '/'

    def run(self):
        self.data = dict()

        for gatherer in self.info_gatherers:
            gatherer()

        self.output = {
            'full_text': self.format.format(**self.data)
        }
        if self.color:
            self.output['color'] = self.color

    @staticmethod
    def parse_clk_reading(reading):
        for l in reading.splitlines():
            if l.endswith('*'):
                return l.split(' ')[1]

    def get_mclk(self):
        with open(self.dev_path + 'pp_dpm_mclk') as f:
            self.data['mclk'] = self.parse_clk_reading(f.read())

    def get_sclk(self):
        with open(self.dev_path + 'pp_dpm_sclk') as f:
            self.data['sclk'] = self.parse_clk_reading(f.read())

    def get_temp(self):
        with open(self.hwmon_path + 'temp1_input') as f:
            self.data['temp'] = float(f.read()) / 1000

    def get_fan_speed(self):
        with open(self.hwmon_path + 'fan1_input') as f:
            self.data['fan_speed'] = f.read().strip()

    def get_gpu_usage(self):
        with open(self.dev_path + 'gpu_busy_percent') as f:
            self.data['gpu_usage'] = f.read().strip()
