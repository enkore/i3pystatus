from subprocess import check_output, CalledProcessError
import subprocess
from i3pystatus import logger
# class Command(Object):

# ,*args
def run_through_shell(command,enable_log):
    """
    Retrieves output of shell command
    Returns tuple boolean (success)/ string (error msg, output)
    """
    result=False
    try:
        #stderr=subprocess.STDOUT
        #stderr=subprocess.PIPE
        # with subprocess.Popen() as proc:
        #   logger.error(proc.stderr.read())
        proc = subprocess.Popen(command,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
             
        out, stderr = proc.communicate()
        if stderr and enable_log:
            logger.error(stderr)
        # out = check_output(command, stderr=subprocess.STDOUT, shell=True)
        result=True
        # color = self.color
    except CalledProcessError as e:
        out = e.output
        # color = self.error_color

    out = out.decode("UTF-8").replace("\n", " ")
    try:
        if out[-1] == " ":
            out = out[:-1]
    except:
        out = ""

    return result, out
