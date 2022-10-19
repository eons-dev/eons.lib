import sys, os
import argparse
import logging
import requests
import jsonpickle
from pathlib import Path
from tqdm import tqdm
from zipfile import ZipFile
from distutils.dir_util import mkpath
from .Constants import *
from .Exceptions import *
from .DataContainer import DataContainer
from .Functor import Functor
from .SelfRegistering import SelfRegistering
from .Recoverable import recoverable
from .Utils import util

# Executor: a base class for user interfaces.
# An Executor is a functor and can be executed as such.
# For example
#	class MyExecutor(Executor):
#		def __init__(this):
#			super().__init__()
#	. . .
#	myprogram = MyExecutor()
#	myprogram()
# NOTE: Diamond inheritance of Datum.
class Executor(DataContainer, Functor):

	def __init__(this, name=INVALID_NAME(), descriptionStr="eons python framework. Extend as thou wilt."):
		this.SetupLogging()

		super().__init__(name)

		# Error resolution configuration.
		this.resolveErrors = True
		this.errorRecursionDepth = 0
		this.errorResolutionStack = {}
		this.resolveErrorsWith = [ # order matters: FIFO (first is first).
			'install_from_repo',
			'install_with_pip'
		]

		# Caching is required for Functor's staticKWArgs and other static features to be effective.
		# This is used in Execute().
		this.cachedFunctors = {}

		# General system info
		this.cwd = os.getcwd()
		this.syspath = sys.path  # not used atm.

		# CLI (or otherwise) args
		this.argparser = argparse.ArgumentParser(description = descriptionStr)
		this.parsedArgs = None
		this.extraArgs = None
		
		# How much information should we output?
		this.verbosity = 0

		# config is loaded with the contents of a JSON config file specified by --config / -c or by the defaultConfigFile location, below.
		this.config = None

		# Where should we log to?
		# Set by Fetch('log_file')
		this.log_file = None

		# All repository configuration.
		this.repo = util.DotDict()

		# Defaults.
		# You probably want to configure these in your own Executors.
		this.defaultRepoDirectory = os.path.abspath(os.path.join(os.getcwd(), "./eons/"))
		this.registerDirectories = []
		this.defaultConfigFile = None

		this.defaultPrefix = ""

		this.Configure()
		this.RegisterIncludedClasses()
		this.AddArgs()


	# Adapter for @recoverable.
	# See Recoverable.py for details
	def GetExecutor(this):
		return this


	# this.errorResolutionStack are whatever we've tried to do to fix whatever our problem is.
	# This method resets our attempts to remove stale data.
	def ClearErrorResolutionStack(this, force=False):
		if (force):
			this.errorRecursionDepth = 0

		if (this.errorRecursionDepth):
			this.errorRecursionDepth = this.errorRecursionDepth - 1

		if (not this.errorRecursionDepth):
			this.errorResolutionStack = {}


	# Configure class defaults.
	# Override this to customize your Executor.
	def Configure(this):
		this.fetchFrom.remove('executor') # No no no no!
		this.fetchFrom.remove('precursor') # Not applicable here.

		# Usually, Executors shunt work off to other Functors, so we leave these True unless a child needs to check its work.
		this.functionSucceeded = True
		this.rollbackSucceeded = True


	# Add a place to search for SelfRegistering classes.
	# These should all be relative to the invoking working directory (i.e. whatever './' is at time of calling Executor())
	def RegisterDirectory(this, directory):
		this.registerDirectories.append(os.path.abspath(os.path.join(this.cwd,directory)))


	# Global logging config.
	# Override this method to disable or change.
	# This method will add a 'setupBy' member to the root logger in order to ensure no one else (e.g. another Executor) tries to reconfigure the logger while we're using it.
	# The 'setupBy' member will be removed from the root logger by TeardownLogging, which is called in AfterFunction().
	def SetupLogging(this):
		class CustomFormatter(logging.Formatter):

			preFormat = util.console.GetColorCode('white', 'dark') + '%(asctime)s'
			format = ' [%(levelname)4s] %(message)s '
			postFormat = util.console.GetColorCode('white', 'dark') + '(%(filename)s:%(lineno)s)' + util.console.resetStyle

			formats = {
				logging.DEBUG: preFormat + util.console.GetColorCode('cyan', 'dark') + format + postFormat,
				logging.INFO: preFormat + util.console.GetColorCode('white', 'light') + format + postFormat,
				logging.WARNING: preFormat + util.console.GetColorCode('yellow', 'light') + format + postFormat,
				logging.ERROR: preFormat + util.console.GetColorCode('red', 'dark') + format + postFormat,
				logging.CRITICAL: preFormat + util.console.GetColorCode('red', 'light', styles=['bold']) + format + postFormat
			}

			def format(this, record):
				log_fmt = this.formats.get(record.levelno)
				formatter = logging.Formatter(log_fmt, datefmt = '%H:%M:%S')
				return formatter.format(record)

		# Skip setting up logging if it's already been done.
		if (hasattr(logging.getLogger(), 'setupBy')):
			return

		logging.getLogger().handlers.clear()
		stderrHandler = logging.StreamHandler()
		stderrHandler.setLevel(logging.CRITICAL)
		stderrHandler.setFormatter(CustomFormatter())
		logging.getLogger().addHandler(stderrHandler)
		setattr(logging.getLogger(), 'setupBy', this)


	# Global logging de-config.
	def TeardownLogging(this):
		if (not hasattr(logging.getLogger(), 'setupBy')):
			return
		if (not logging.getLogger().setupBy == this):
			return
		delattr(logging.getLogger(), 'setupBy')



	# Logging to stderr is easy, since it will always happen.
	# However, we also want the user to be able to log to a file, possibly set in the config.json, which requires a Fetch().
	# Thus, setting up the log file handler has to occur later than the initial SetupLogging call.
	# Calling this multiple times will add multiple log handlers.
	def SetLogFile(this):
		this.Set('log_file', this.Fetch('log_file', None, ['args', 'config', 'environment']))
		if (this.log_file is None):
			return

		log_filePath = Path(this.log_file).resolve()
		if (not log_filePath.exists()):
			log_filePath.parent.mkdir(parents=True, exist_ok=True)
			log_filePath.touch()

		this.log_file = str(log_filePath) # because resolve() is nice.
		logging.info(f"Will log to {this.log_file}")

		logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)')
		fileHandler = logging.FileHandler(this.log_file)
		fileHandler.setFormatter(logFormatter)
		fileHandler.setLevel(logging.DEBUG)
		logging.getLogger().addHandler(fileHandler)


	# Adds command line arguments.
	# Override this method to change. Optionally, call super().AddArgs() within your method to simply add to this list.
	def AddArgs(this):
		this.argparser.add_argument('--verbose', '-v', action='count', default=0)
		this.argparser.add_argument('--config', '-c', type=str, default=None, help='Path to configuration file containing only valid JSON.', dest='config')

		# We'll use Fetch instead
		# this.argparser.add_argument('--log', '-l', type=str, default=None, help='Path to log file.', dest='log')
		# this.argparser.add_argument('--no-repo', action='store_true', default=False, help='prevents searching online repositories', dest='no_repo')


	# Create any sub-class necessary for child-operations
	# Does not RETURN anything.
	def InitData(this):
		pass


	# Register included files early so that they can be used by the rest of the system.
	# If we don't do this, we risk hitting infinite loops because modular functionality relies on these modules.
	# NOTE: this method needs to be overridden in all children which ship included Functors, Data, etc. This is because __file__ is unique to the eons.py file, not the child's location.
	def RegisterIncludedClasses(this):
		includePaths = [
			'resolve',
		]
		for path in includePaths:
			this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath(path)))


	# Executors should not have precursors
	def PopulatePrecursor(this):
		this.executor = this
		pass


	# Register all classes in each directory in this.registerDirectories
	def RegisterAllClasses(this):
		for d in this.registerDirectories:
			this.RegisterAllClassesInDirectory(os.path.join(os.getcwd(), d))
		this.RegisterAllClassesInDirectory(this.repo.store)


	# Populate the configuration details for *this.
	def PopulateConfig(this):
		this.config = None

		if (this.parsedArgs.config is None):
			this.parsedArgs.config = this.defaultConfigFile

		logging.debug(f"Populating config from {this.parsedArgs.config}")

		if (this.parsedArgs.config is None):
			return

		if (not os.path.isfile(this.parsedArgs.config)):
			logging.error(f"Could not open configuration file: {this.parsedArgs.config}")
			return

		configFile = open(this.parsedArgs.config, "r")
		this.config = jsonpickle.decode(configFile.read())
		configFile.close()


	#  Get information for how to download packages.
	def PopulateRepoDetails(this):
		details = {
			"online": not this.Fetch('no_repo', False, ['this', 'args', 'config']),
			"store": this.defaultRepoDirectory,
			"url": "https://api.infrastructure.tech/v1/package",
			"username": None,
			"password": None
		}
		for key, default in details.items():
			this.repo[key] = this.Fetch(f"repo_{key}", default=default)


	# How do we get the verbosity level and what do we do with it?
	# This method should set log levels, etc.
	def SetVerbosity(this):

		# Take the highest of -v vs --verbosity
		verbosity = this.Fetch('verbosity', 0, ['args', 'config', 'environment'])
		if (verbosity > this.verbosity):
			logging.debug(f"Setting verbosity to {verbosity}") # debug statements will be available when using external systems, like pytest.
			this.verbosity = verbosity

		if (this.parsedArgs.verbose == 1):
			logging.getLogger().handlers[0].setLevel(logging.WARNING)
			logging.getLogger().setLevel(logging.WARNING)
		elif (this.parsedArgs.verbose == 2):
			logging.getLogger().handlers[0].setLevel(logging.INFO)
			logging.getLogger().setLevel(logging.INFO)
		elif(this.parsedArgs.verbose >= 3):
			logging.getLogger().handlers[0].setLevel(logging.DEBUG)
			logging.getLogger().setLevel(logging.DEBUG)


	# Do the argparse thing.
	# Extra arguments are converted from --this-format to this_format, without preceding dashes. For example, --repo-url ... becomes repo_url ...
	# NOTE: YOU CANNOT USE @recoverable METHODS HERE!
	def ParseArgs(this):
		this.parsedArgs, extraArgs = this.argparser.parse_known_args()

		this.verbosity = this.parsedArgs.verbose

		extraArgsKeys = []
		for index in range(0, len(extraArgs), 2):
			keyStr = extraArgs[index]
			keyStr = keyStr.replace('--', '').replace('-', '_')
			extraArgsKeys.append(keyStr)

		extraArgsValues = []
		for index in range(1, len(extraArgs), 2):
			extraArgsValues.append(extraArgs[index])

		this.extraArgs = dict(zip(extraArgsKeys, extraArgsValues))

	# Functor method.
	# We have to ParseArgs() here in order for other Executors to use ____KWArgs...
	def ParseInitialArgs(this):
		this.ParseArgs() # first, to enable debug and other such settings.
		this.PopulateConfig()
		this.SetVerbosity()
		this.SetLogFile()
		logging.debug(f"<---- {this.name} (log level: {logging.getLogger().level}) ---->")
		logging.debug(f"Got extra arguments: {this.extraArgs}") # has to be after verbosity setting
		logging.debug(f"Got config contents: {this.config}")
		this.PopulateRepoDetails()


	# Functor required method
	# Override this with your own workflow.
	def Function(this):
		this.RegisterAllClasses()
		this.InitData()


	# By default, Executors do not act on this.next; instead, they make it available to all Executed Functors.
	def CallNext(this):
		pass


	# Close out anything we left open.
	def AfterFunction(this):
		this.TeardownLogging()


	# Execute a Functor based on name alone (not object).
	# If the given Functor has been Executed before, the cached Functor will be called again. Otherwise, a new Functor will be constructed.
	@recoverable
	def Execute(this, functorName, *args, **kwargs):
		prefix = this.defaultPrefix
		if ('prefix' in kwargs):
			prefix = kwargs.pop('prefix')

		logging.debug(f"Executing {functorName}({', '.join([str(a) for a in args] + [k+'='+str(v) for k,v in kwargs.items()])})")

		if (functorName in this.cachedFunctors):
			return this.cachedFunctors[functorName](*args, **kwargs, executor=this)

		functor = this.GetRegistered(functorName, prefix)
		this.cachedFunctors.update({functorName: functor})

		return functor(*args, **kwargs, executor=this)


	# Attempts to download the given package from the repo url specified in calling args.
	# Will refresh registered classes upon success
	# RETURNS whether or not the package was downloaded. Will raise Exceptions on errors.
	# Does not guarantee new classes are made available; errors need to be handled by the caller.
	@recoverable
	def DownloadPackage(this,
		packageName,
		registerClasses=True,
		createSubDirectory=False):

		if (not this.repo.online):
			logging.debug(f"Refusing to download {packageName}; we were told not to use a repository.")
			return False

		logging.debug(f"Trying to download {packageName} from repository ({this.repo.url})")

		if (not os.path.exists(this.repo.store)):
			logging.debug(f"Creating directory {this.repo.store}")
			mkpath(this.repo.store)

		packageZipPath = os.path.join(this.repo.store, f"{packageName}.zip")

		url = f"{this.repo.url}/download?package_name={packageName}"

		auth = None
		if this.repo.username and this.repo.password:
			auth = requests.auth.HTTPBasicAuth(this.repo.username, this.repo.password)

		headers = {
			"Connection": "keep-alive",
		}

		packageQuery = requests.get(url, auth=auth, headers=headers, stream=True)

		if (packageQuery.status_code != 200):
			raise PackageError(f"Unable to download {packageName}")
		# let caller decide what to do next.

		packageSize = int(packageQuery.headers.get('content-length', 0))
		chunkSize = 1024 # 1 Kibibyte

		logging.debug(f"Writing {packageZipPath} ({packageSize} bytes)")
		packageZipContents = open(packageZipPath, 'wb+')

		progressBar = None
		if (this.verbosity >= 2):
			progressBar = tqdm(total=packageSize, unit='iB', unit_scale=True)

		for chunk in packageQuery.iter_content(chunkSize):
			packageZipContents.write(chunk)
			if (this.verbosity >= 2):
				progressBar.update(len(chunk))

		if (this.verbosity >= 2):
			progressBar.close()

		if (packageSize and this.verbosity >= 2 and progressBar.n != packageSize):
			raise PackageError(f"Package wrote {progressBar.n} / {packageSize} bytes")

		packageZipContents.close()

		if (not os.path.exists(packageZipPath)):
			raise PackageError(f"Failed to create {packageZipPath}")

		logging.debug(f"Extracting {packageZipPath}")
		openArchive = ZipFile(packageZipPath, 'r')
		extractLoc = this.repo.store
		if (createSubDirectory):
			extractLoc = os.path.join(extractLoc, packageName)
		openArchive.extractall(f"{extractLoc}")
		openArchive.close()
		os.remove(packageZipPath)

		if (registerClasses):
			this.RegisterAllClassesInDirectory(this.repo.store)

		return True

	# RETURNS and instance of a Datum, Functor, etc. (aka modules) which has been discovered by a prior call of RegisterAllClassesInDirectory()
	# Will attempt to register existing modules if one of the given name is not found. Failing that, the given package will be downloaded if it can be found online.
	# Both python modules and other eons modules of the same prefix will be installed automatically in order to meet all required dependencies of the given module.
	@recoverable
	def GetRegistered(this,
		registeredName,
		prefix=""):

		try:
			registered = SelfRegistering(registeredName)
		except Exception as e:
			# We couldn't get what was asked for. Let's try asking for help from the error resolution machinery.
			packageName = registeredName
			if (prefix):
				packageName = f"{prefix}_{registeredName}"
			logging.error(f"While trying to instantiate {packageName}, got: {e}")
			raise HelpWantedWithRegistering(f"Trying to get SelfRegistering {packageName}")

		# NOTE: Functors are Data, so they have an IsValid() method
		if (not registered or not registered.IsValid()):
			logging.error(f"No valid object: {registeredName}")
			raise FatalCannotExecute(f"No valid object: {registeredName}")

		return registered


	# Non-static override of the SelfRegistering method.
	# Needed for errorObject resolution.
	@recoverable
	def RegisterAllClassesInDirectory(this, directory):
		path = Path(directory)
		if (not path.exists()):
			logging.debug(f"Making path for SelfRegitering classes: {str(path)}")
			path.mkdir(parents=True, exist_ok=True)

		if (directory not in this.syspath):
			this.syspath.append(directory)

		SelfRegistering.RegisterAllClassesInDirectory(directory)


	# Utility method. may not be useful.
	@staticmethod
	def SplitNameOnPrefix(name):
		splitName = name.split('_')
		if (len(splitName)>1):
			return splitName[0], splitName[1]
		return "", name


	# Uses the ResolveError Functors to process any errors.
	@recoverable
	def ResolveError(this, error, attemptResolution):
		if (attemptResolution >= len(this.resolveErrorsWith)):
			raise FailedErrorResolution(f"{this.name} does not have {attemptResolution} resolutions to fix this error: {error} (it has {len(this.resolveErrorsWith)})")

		resolution = this.GetRegistered(this.resolveErrorsWith[attemptResolution], "resolve") # Okay to ResolveErrors for ErrorResolutions.
		this.errorResolutionStack, errorMightBeResolved = resolution(executor=this, error=error)
		if (errorMightBeResolved):
			logging.debug(f"Error might have been resolved by {resolution.name}.")
		return errorMightBeResolved


	######## START: Fetch Locations ########

	def fetch_location_args(this, varName, default, fetchFrom, attempted):
		for key, val in this.extraArgs.items():
			if (key == varName):
				return val, True
		return default, False

	######## END: Fetch Locations ########
