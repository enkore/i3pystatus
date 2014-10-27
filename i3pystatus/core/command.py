from i3pystatus import IntervalModule
from subprocess import check_output, CalledProcessError


class Command(object):

    args = []
    command = ""
    def __init__(self, command, *args,**kwargs):
        self.args = args;
        self.command = command

    def run(self, module):
        """
        Returns tuple boolean (success)/ string (error msg, output)
        """
       
        

        # if it is a python fct, then run it
        if callable(self.command):
            self.command(self.args)
        #
        elif hasattr(module,self.command):
            pass
        # it it is a string (as a last resort, then run the process with args
        else:
            return self.run_through_shell(self.command)

    # def __call__(self):

    @staticmethod
    # def run_through_shell(module, member,*args):


    @staticmethod
    def run_through_shell(command,*args):
        """
        Retrieves output of shell command
        Returns tuple boolean (success)/ string (error msg, output)
        """
        result=False
        try:
            out = check_output(command, shell=True)
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

        # self.output = {
        #     "full_text": out,
        #     "color": color
        # }

