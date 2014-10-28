from i3pystatus import IntervalModule
from subprocess import check_output, CalledProcessError


class Command(object):

    args = None
    kwargs= None
    command = ""
    def __init__(self, command, *args,**kwargs):
        self.args = args;
        self.kwargs = kwargs
        self.command = command

    def run(self, module):
        """
        Returns tuple boolean (success)/ string (error msg, output)
        """
       
        # print("RUN")

        # if it is a python fct, then run it
        if callable(self.command):
            self.command(*self.args)
        #
        elif hasattr(module,self.command):
            getattr(module,self.command)(*self.args,**self.kwargs)
        # it it is a string (as a last resort, then run the process with args
        else:
            return self.run_through_shell(self.command)

    # def __call__(self):

    
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

