import logging
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

    if not enable_shell and not isinstance(command, list):
        command = command.split()

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
        logging.getLogger("i3pystatus.core.command").exception("")
    except subprocess.CalledProcessError as e:
        out = e.output
        logging.getLogger("i3pystatus.core.command").exception("")

    return CommandResult(returncode, out, stderr)


def execute(command, detach=False):
    """
    Runs a command in background.
    No output is retrieved.
    Useful for running GUI applications that would block click events.

    :param detach If set to `True` the application will be executed using the
    `i3-msg` command (survives i3 in-place restart).
    """

    if not isinstance(command, list):
        command = command.split()

    if detach:
        command.insert(0, "exec")
        command.insert(0, "i3-msg")

    try:
        subprocess.Popen(command, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        logging.getLogger("i3pystatus.core.command").exception("")
    except subprocess.CalledProcessError:
        logging.getLogger("i3pystatus.core.command").exception("")
