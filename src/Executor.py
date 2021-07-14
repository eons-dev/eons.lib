import sys, os
import argparse
import logging
from .Constants import *
from .DataContainer import DataContainer
from .UserFunctor import UserFunctor
from .SelfRegistering import SelfRegistering

#Executor: a base class for user interfaces.
#An Executor is a functor and can be executed as such.
#For example
#   class MyExecutor(Executor):
#       def __init__(self):
#           super().__init__()
#   . . .
#   myprogram = MyExecutor()
#   myprogram()
#NOTE: Diamond inheritance of Datum.
class Executor(DataContainer, UserFunctor):

    def __init__(self, name=INVALID_NAME(), descriptionStr="eons python framework. Extend as thou wilt."):
        self.SetupLogging()
        
        super().__init__(name)
        
        self.argparser = argparse.ArgumentParser(description = descriptionStr)
        self.args = None
        self.AddArgs()

        self.registerDirectories = []
        
    #Add a place to search for SelfRegistering classes.
    #These should all be relative to the invoking working directory (i.e. whatever './' is at time of calling Executor())
    def RegisterDirectory(self, directory):
        self.registerDirectories.append(directory)
        
    #Global logging config.
    #Override this method to disable or change.
    def SetupLogging(self):
        logging.basicConfig(level = logging.INFO, format = '%(asctime)s [%(levelname)-8s] - %(message)s (%(filename)s:%(lineno)s)', datefmt = '%H:%M:%S')

    #Adds command line arguments.
    #Override this method to change. Optionally, call super().AddArgs() within your method to simply add to this list.
    def AddArgs(self):
        self.argparser.add_argument('--verbose', '-v', action='count', default=1)

    #Create any sub-data necessary for child-operations
    #Does not RETURN anything.
    def InitData(self):
        pass
        
    #Register all classes in each directory in self.registerDirectories
    def RegisterAllClasses(self):
        for d in self.registerDirectories:
            RegisterAllClassesInDirectory(os.path.join(os.getcwd(), d))

    #Something went wrong, let's quit.
    #TODO: should this simply raise an exception?
    def ExitDueToErr(self, errorStr):
        # logging.info("#################################################################\n")
        logging.error(errorStr)
        # logging.info("\n#################################################################")
        self.argparser.print_help()
        sys.exit()

    #Do the argparse thing.
    def ParseArgs(self):
        self.args = self.argparser.parse_args()

        if (self.args.verbose > 0): #TODO: different log levels with -vv, etc.?
            logging.getLogger().setLevel(logging.DEBUG)

    #UserFunctor required method
    #Override this with your own workflow.
    def UserFunction(self, **kwargs):
        self.RegisterAllClasses()
        self.InitData()
        self.ParseArgs()

    #RETURNS and instance of a Datum, UserFunctor, etc. which has been discovered by a prior call of RegisterAllClassesInDirectory()
    def GetRegistered(self, registeredName):
        registered = SelfRegistering(registeredName)
        if (not registered or not registered.IsValid()): #UserFunctors are Data, so everything should have an IsValid() method
            self.ExitDueToErr(f"{registeredName} not found.")
        return registered
