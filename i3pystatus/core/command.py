from subprocess import CalledProcessError
import subprocess
from i3pystatus import logger


def run_through_shell(command, enable_log, enable_shell=False):
    """
    Retrieves output of shell command
    Returns tuple boolean (success)/ string (error msg, output)
    """
    result = False
    try:
        proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=enable_shell)

        out, stderr = proc.communicate()
        if stderr and enable_log:
            logger.error(stderr)

        result = True

    except CalledProcessError as e:
        out = e.output
        # color = self.error_color

    out = out.decode("UTF-8").replace("\n", " ")
    try:
        if out[-1] == " ":
            out = out[:-1]
    except:
        out = ""

    return out, result
