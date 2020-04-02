import subprocess
from collections import namedtuple
from typing import Optional

GPUUsageInfo = namedtuple('GPUUsageInfo', ['total_mem', 'avail_mem', 'used_mem',
                                           'temp', 'percent_fan',
                                           'usage_gpu', 'usage_mem'])


def _convert_nvidia_smi_value(value) -> Optional[int]:
    value = value.lower()
    # If value contains 'not' or 'N/A' - it is not supported for this GPU
    # (in fact, for now nvidia-smi returns '[Not Supported]' or '[N/A]' depending of its version)
    if "not" in value or "n/a" in value:
        return None
    return int(value)


def query_nvidia_smi(gpu_number) -> GPUUsageInfo:
    """
    :return:
        all memory fields are in megabytes,
        temperature in degrees celsius,
        fan speed is integer percent from 0 to 100 inclusive,
        usage_gpu and usage_mem are integer percents from 0 to 100 inclusive
        (usage_mem != used_mem, usage_mem is about read/write access load)
        read more in 'nvidia-smi --help-query-gpu'.

        Any field can be None if such information is not supported by nvidia-smi for current GPU

        Returns None if call failed (no nvidia-smi or query format was changed)

        Raises exception with readable comment
    """
    params = ["memory.total", "memory.free", "memory.used",
              "temperature.gpu", "fan.speed",
              "utilization.gpu", "utilization.memory"]
    try:
        output = subprocess.check_output(["nvidia-smi",
                                          "--query-gpu={}".format(','.join(params)),
                                          "--format=csv,noheader,nounits"])
    except FileNotFoundError:
        raise Exception("No nvidia-smi")
    except subprocess.CalledProcessError:
        raise Exception("nvidia-smi call failed")

    output = output.decode('utf-8').split("\n")[gpu_number].strip()
    values = output.split(", ")

    values = [_convert_nvidia_smi_value(value) for value in values]

    return GPUUsageInfo(*values)
