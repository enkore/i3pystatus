
from pkgutil import extend_path

from i3pystatus.core import Status
from i3pystatus.core.modules import Module, IntervalModule
from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.util import formatp

__path__ = extend_path(__path__, __name__)
