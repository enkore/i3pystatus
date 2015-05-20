# from subprocess import CalledProcessError
from collections import namedtuple
import subprocess

CommandResult = namedtuple("Result", ['rc', 'out', 'err'])


def run_through_shell(command, enable_shell=False):
    """
    Retrieves output of command
    Returns tuple success (boolean)/ stdout(string) / stderr (string)

    Don't use this function with programs that outputs lots of data since the output is saved
    in one variable
    """

    returncode = None
    stderr = None
    try:
        proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=enable_shell)
        out, stderr = proc.communicate()
        out = out.decode("UTF-8")
        stderr = stderr.decode("UTF-8")

        returncode = proc.returncode

    except OSError as e:
        out = e.strerror
        stderr = e.strerror
    except subprocess.CalledProcessError as e:
        out = e.output

    return CommandResult(returncode, out, stderr)
