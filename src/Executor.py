import sys, os
import argparse
import logging
import requests
import jsonpickle
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
#       def __init__(this):
#           super().__init__()
#   . . .
#   myprogram = MyExecutor()
#   myprogram()
#NOTE: Diamond inheritance of Datum.
class Executor(DataContainer, UserFunctor):

    def __init__(this, name=INVALID_NAME(), descriptionStr="eons python framework. Extend as thou wilt."):
        this.SetupLogging()

        super().__init__(name)

        this.cwd = os.getcwd()
        this.Configure()
        this.argparser = argparse.ArgumentParser(description = descriptionStr)
        this.args = None
        this.extraArgs = None
        this.AddArgs()


    #Configure class defaults.
    #Override this to customize your Executor.
    def Configure(this):
        this.defaultRepoDirectory = os.path.abspath(os.path.join(this.cwd, "./eons/"))
        this.registerDirectories = []
        this.defualtConfigFile = None


    #Add a place to search for SelfRegistering classes.
    #These should all be relative to the invoking working directory (i.e. whatever './' is at time of calling Executor())
    def RegisterDirectory(this, directory):
        this.registerDirectories.append(os.path.abspath(os.path.join(this.cwd,directory)))


    #Global logging config.
    #Override this method to disable or change.
    def SetupLogging(this):
        logging.basicConfig(level = logging.INFO, format = '%(asctime)s [%(levelname)-8s] - %(message)s (%(filename)s:%(lineno)s)', datefmt = '%H:%M:%S')


    #Adds command line arguments.
    #Override this method to change. Optionally, call super().AddArgs() within your method to simply add to this list.
    def AddArgs(this):
        this.argparser.add_argument('--verbose', '-v', action='count', default=0)
        this.argparser.add_argument('--config', '-c', type=str, default=None, help='Path to configuration file containing only valid JSON.', dest='config')
        this.argparser.add_argument('--no-repo', action='store_true', default=False, help='prevents searching online repositories', dest='no_repo')

    #Create any sub-class necessary for child-operations
    #Does not RETURN anything.
    def InitData(this):
        pass


    #Register all classes in each directory in this.registerDirectories
    def RegisterAllClasses(this):
        for d in this.registerDirectories:
            this.RegisterAllClassesInDirectory(os.path.join(os.getcwd(), d))


    #Something went wrong, let's quit.
    #TODO: should this simply raise an exception?
    def ExitDueToErr(this, errorStr):
        # logging.info("#################################################################\n")
        logging.error(errorStr)
        # logging.info("\n#################################################################")
        this.argparser.print_help()
        sys.exit()


    #Populate the configuration details for *this.
    def PopulateConfig(this):
        this.config = None

        if (this.args.config is None):
            this.args.config = this.defualtConfigFile

        if (this.args.config is not None and os.path.isfile(this.args.config)):
            configFile = open(this.args.config, "r")
            this.config = jsonpickle.decode(configFile.read())
            configFile.close()
            logging.debug(f"Got config contents: {this.config}")


    # Get information for how to download packages.
    def PopulateRepoDetails(this):
        details = {
            "store": this.defaultRepoDirectory,
            "url": "https://api.infrastructure.tech/v1/package",
            "username": None,
            "password": None
        }
        this.repo = {}

        if (this.args.no_repo is not None and this.args.no_repo):
            for key, default in details.items():
                this.repo[key] = None
        else:
            for key, default in details.items():
                this.repo[key] = this.Fetch(f"repo_{key}", default=default)


    #Do the argparse thing.
    #Extra arguments are converted from --this-format to this_format, without preceding dashes. For example, --repo-url ... becomes repo_url ... 
    def ParseArgs(this):
        this.args, extraArgs = this.argparser.parse_known_args()

        extraArgsKeys = []
        for index in range(0, len(extraArgs), 2):
            keyStr = extraArgs[index]
            keyStr.replace('--', '').replace('-', '_')
            extraArgsKeys.append(keyStr)

        extraArgsValues = []
        for index in range(1, len(extraArgs), 2):
            extraArgsValues.append(extraArgs[index])

        this.extraArgs = dict(zip(extraArgsKeys, extraArgsValues))

        if (this.args.verbose > 0): #TODO: different log levels with -vv, etc.?
            logging.getLogger().setLevel(logging.DEBUG)


    # Will try to get a value for the given varName from:
    #    first: this.
    #    second: extra arguments provided to *this.
    #    third: the config file, if provided.
    #    fourth: the environment (if enabled).
    # RETURNS the value of the given variable or None.
    def Fetch(this, varName, default=None, enableSelf=True, enableArgs=True, enableConfig=True, enableEnvironment=True):
        logging.debug(f"Fetching {varName}...")

        if (enableSelf and hasattr(this, varName)):
            logging.debug(f"...got {varName} from {this.name}.")
            return getattr(this, varName)

        if (enableArgs):
            for key, val in this.extraArgs.items():
                if (key == varName):
                    logging.debug(f"...got {varName} from argument.")
                    return val

        if (enableConfig and this.config is not None):
            for key, val in this.config.items():
                if (key == varName):
                    logging.debug(f"...got {varName} from config.")
                    return val

        if (enableEnvironment):
            envVar = os.getenv(varName)
            if (envVar is not None):
                logging.debug(f"...got {varName} from environment")
                return envVar

        logging.debug(f"...could not find {varName}; using default ({default})")
        return None

        
    #UserFunctor required method
    #Override this with your own workflow.
    def UserFunction(this, **kwargs):
        this.ParseArgs() #first, to enable debug and other such settings.
        this.PopulateConfig()
        this.PopulateRepoDetails()
        this.RegisterAllClasses()
        this.InitData()


    #Attempts to download the given package from the repo url specified in calling args.
    #Will refresh registered classes upon success
    #RETURNS void
    #Does not guarantee new classes are made available; errors need to be handled by the caller.
    def DownloadPackage(this, packageName, registerClasses=True, createSubDirectory=False):

        if (this.args.no_repo is not None and this.args.no_repo):
            logging.debug(f"Refusing to download {packageName}; we were told not to use a repository.")
            return

        url = f"{this.repo['url']}/download?package_name={packageName}"

        auth = None
        if this.repo['username'] and this.repo['password']:
            auth = requests.auth.HTTPBasicAuth(this.repo['username'], this.repo['password'])

        packageQuery = requests.get(url, auth=auth)

        if (packageQuery.status_code != 200 or not len(packageQuery.content)):
            logging.error(f"Unable to download {packageName}")
            #TODO: raise error?
            return #let caller decide what to do next.

        if (not os.path.exists(this.repo['store'])):
            logging.debug(f"Creating directory {this.repo['store']}")
            mkpath(this.repo['store'])

        packageZip = os.path.join(this.repo['store'], f"{packageName}.zip")

        logging.debug(f"Writing {packageZip}")
        openPackage = open(packageZip, 'wb+')
        openPackage.write(packageQuery.content)
        openPackage.close()
        if (not os.path.exists(packageZip)):
            logging.error(f"Failed to create {packageZip}")
            # TODO: raise error?
            return

        logging.debug(f"Extracting {packageZip}")
        openArchive = ZipFile(packageZip, 'r')
        extractLoc = this.repo['store']
        if (createSubDirectory):
            extractLoc = os.path.join(extractLoc, packageName)
        openArchive.extractall(f"{extractLoc}")
        openArchive.close()
        os.remove(packageZip)
        
        if (registerClasses):
            this.RegisterAllClassesInDirectory(this.repo['store'])

    #RETURNS and instance of a Datum, UserFunctor, etc. which has been discovered by a prior call of RegisterAllClassesInDirectory()
    def GetRegistered(this, registeredName, prefix=""):

        #Start by looking at what we have.
        try:
            registered = SelfRegistering(registeredName)

        except Exception as e:

            #Then try registering what's already downloaded.
            try:
                this.RegisterAllClassesInDirectory(this.repo['store'])
                registered = SelfRegistering(registeredName)

            except Exception as e2:

                logging.debug(f"{registeredName} not found.")
                packageName = registeredName
                if (prefix):
                    packageName = f"{prefix}_{registeredName}"
                logging.debug(f"Trying to download {packageName} from repository ({this.repo['url']})")
                this.DownloadPackage(packageName)
                registered = SelfRegistering(registeredName)

        #NOTE: UserFunctors are Data, so they have an IsValid() method
        if (not registered or not registered.IsValid()):
            logging.error(f"Could not find {registeredName}")
            raise Exception(f"Could not get registered class for {registeredName}")

        return registered

