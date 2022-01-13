import sys, os
import argparse
import logging
import requests
from zipfile import ZipFile
from distutils.dir_util import mkpath
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

        self.cwd = os.getcwd()
        self.Configure()
        self.argparser = argparse.ArgumentParser(description = descriptionStr)
        self.args = None
        self.extraArgs = None
        self.AddArgs()

    #Configure class defaults.
    #Override this to customize your Executor.
    def Configure(self):
        self.defaultRepoDirectory = os.path.abspath(os.path.join(self.cwd, "./eons/"))
        self.registerDirectories = []

    #Add a place to search for SelfRegistering classes.
    #These should all be relative to the invoking working directory (i.e. whatever './' is at time of calling Executor())
    def RegisterDirectory(self, directory):
        self.registerDirectories.append(os.path.abspath(os.path.join(self.cwd,directory)))

    #Global logging config.
    #Override this method to disable or change.
    def SetupLogging(self):
        logging.basicConfig(level = logging.INFO, format = '%(asctime)s [%(levelname)-8s] - %(message)s (%(filename)s:%(lineno)s)', datefmt = '%H:%M:%S')

    #Adds command line arguments.
    #Override this method to change. Optionally, call super().AddArgs() within your method to simply add to this list.
    def AddArgs(self):
        self.argparser.add_argument('--verbose', '-v', action='count', default=0)
        self.argparser.add_argument('--no-repo', action='store_true', default=False, help='prevents searching online repositories', dest='no_repo')
        self.argparser.add_argument('--repo-store', type=str, default=self.defaultRepoDirectory, help='file path for storing downloaded packages', dest='repo_store')
        self.argparser.add_argument('--repo-url', type=str, default='https://api.infrastructure.tech/v1/package', help = 'package repository for additional languages', dest='repo_url')
        self.argparser.add_argument('--repo-username', type=str, help='username for http basic auth', dest='repo_username')
        self.argparser.add_argument('--repo-password', type=str, help='password for http basic auth', dest='repo_password')

    #Create any sub-class necessary for child-operations
    #Does not RETURN anything.
    def InitData(self):
        pass

    #Register all classes in each directory in self.registerDirectories
    def RegisterAllClasses(self):
        for d in self.registerDirectories:
            self.RegisterAllClassesInDirectory(os.path.join(os.getcwd(), d))

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
        self.args, extraArgs = self.argparser.parse_known_args()

        extraArgsKeys = []
        for index in range(0, len(extraArgs), 2):
            extraArgsKeys.append(extraArgs[index])

        extraArgsValues = []
        for index in range(1, len(extraArgs), 2):
            extraArgsValues.append(extraArgs[index])

        self.extraArgs = dict(zip(extraArgsKeys, extraArgsValues))

        if (self.args.verbose > 0): #TODO: different log levels with -vv, etc.?
            logging.getLogger().setLevel(logging.DEBUG)

    #UserFunctor required method
    #Override this with your own workflow.
    def UserFunction(self, **kwargs):
        self.ParseArgs() #first, to enable debug and other such settings.
        self.RegisterAllClasses()
        self.InitData()

    #Attempts to download the given package from the repo url specified in calling args.
    #Will refresh registered classes upon success
    #RETURNS void
    #Does not guarantee new classes are made available; errors need to be handled by the caller.
    def DownloadPackage(self, packageName, registerClasses=True):

        url = f'{self.args.repo_url}/download?package_name={packageName}'

        auth = None
        if self.args.repo_username and self.args.repo_password:
            auth = requests.auth.HTTPBasicAuth(self.args.repo_username, self.args.repo_password)

        packageQuery = requests.get(url, auth=auth)

        if (packageQuery.status_code != 200 or not len(packageQuery.content)):
            logging.error(f'Unable to download {packageName}')
            #TODO: raise error?
            return #let caller decide what to do next.

        if (not os.path.exists(self.args.repo_store)):
            logging.debug(f'Creating directory {self.args.repo_store}')
            mkpath(self.args.repo_store)

        packageZip = os.path.join(self.args.repo_store, f'{packageName}.zip')

        logging.debug(f'Writing {packageZip}')
        openPackage = open(packageZip, 'wb+')
        openPackage.write(packageQuery.content)
        openPackage.close()
        if (not os.path.exists(packageZip)):
            logging.error(f'Failed to create {packageZip}')
            # TODO: raise error?
            return

        logging.debug(f'Extracting {packageZip}')
        openArchive = ZipFile(packageZip, 'r')
        openArchive.extractall(f'{self.args.repo_store}')
        openArchive.close()
        os.remove(packageZip)
        
        if (registerClasses):
            self.RegisterAllClassesInDirectory(self.args.repo_store)

    #RETURNS and instance of a Datum, UserFunctor, etc. which has been discovered by a prior call of RegisterAllClassesInDirectory()
    def GetRegistered(self, registeredName, prefix=""):

        #Start by looking at what we have.
        try:
            registered = SelfRegistering(registeredName)
        except Exception as e:

            #Then try registering what's already downloaded.
            try:
                self.RegisterAllClassesInDirectory(self.args.repo_store)
                registered = SelfRegistering(registeredName)
            except Exception as e2:

                #If we're not going to attempt a download, fail.
                if (self.args.no_repo):
                    raise e2

                logging.debug(f'{registeredName} not found.')
                packageName = registeredName
                if (prefix):
                    packageName = f'{prefix}_{registeredName}'
                logging.debug(f'Trying to download {packageName} from repository ({self.args.repo_url})')
                self.DownloadPackage(packageName)
                registered = SelfRegistering(registeredName)

        #NOTE: UserFunctors are Data, so they have an IsValid() method
        if (not registered or not registered.IsValid()):
            logging.error(f'Could not find {registeredName}')
            raise Exception(f'Could not get registered class for {registeredName}')

        return registered

