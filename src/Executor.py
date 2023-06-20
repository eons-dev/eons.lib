import sys, os
import builtins
import argparse
import logging
import requests
import jsonpickle
import yaml
from requests_futures.sessions import FuturesSession
from pathlib import Path
from tqdm import tqdm
from zipfile import ZipFile
from distutils.dir_util import mkpath
from eot import EOT
from .Constants import *
from .Exceptions import *
from .DataContainer import DataContainer
from .Functor import Functor
from .SelfRegistering import SelfRegistering
from .Recoverable import recoverable
from .Utils import util
from .ExecutorTracker import ExecutorTracker
from .FunctorTracker import FunctorTracker

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

	def __init__(this, name=INVALID_NAME(), descriptionStr="Eons python framework. Extend as thou wilt."):
		this.SetupLogging()

		super().__init__(name)

		this.optionalKWArgs['log_time_stardate'] = True
		this.optionalKWArgs['log_indentation'] = True
		this.optionalKWArgs['log_tab_width'] = 2
		this.optionalKWArgs['log_aggregate'] = True
		this.optionalKWArgs['log_aggregate_url'] = "https://eons.sh/log"

		this.resolveErrors = True
		this.errorRecursionDepth = 0
		this.errorResolutionStack = {}
		this.resolveErrorsWith = [ # order matters: FIFO (first is first).
			'find_by_fetch',
			'install_from_repo_with_default_package_type',
			'install_from_repo',
			'import_module',
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
		this.configType = None

		# *this will keep track of any global variables it creates.
		# All globals should be read only.
		# Dict is in the form of {variable_name: set_by_fetch}
		# See SetGlobal(), below.
		this.globals = {}

		# The globalContextKey is mainly used for big, nested configs.
		# It serves as a means of leaving the name of various global values intact while changing their values.
		# For example, a method of some Functor might check service.name, but we might have a service for mysql, redis, etc. In this situation, we can say SetGlobalContextKey('mysql') and the Functor will operate on the mysql.service.name. Then, when we're ready, we SetGlobalContextKey('redis') and call the same Functor again to operate on the redis.service.name.
		# Thus, the globalContextKey allow those using global variables to remain naive of where those values are comming from.
		this.globalContextKey = None

		# Where should we log to?
		# Set by Fetch('log_file')
		this.log_file = None

		# All repository configuration.
		this.repo = util.DotDict()

		# Placement helps to construct the correct load order of Functors as they are installed.
		this.placement = util.DotDict()
		this.placement.max = 255
		this.placement.session = util.DotDict()
		
		# Defaults.
		# You probably want to configure these in your own Executors.
		this.defaultRepoDirectory = os.path.abspath(os.path.join(os.getcwd(), "./eons/"))
		this.registerDirectories = []
		this.defaultConfigFile = None
		this.defaultPackageType = ""

		# Allow the config file to be in multiple formats.
		# These are in preference order (e.g. if you want to look for a .txt file before a .json, add it to the top of the list).
		# Precedence should prefer more structured and machine-generated configs over file formats easier for humans to work with.
		this.configFileExtensions = [
			"json",
			"yaml",
			"yml",
			"py",
		]

		# We can't Fetch from everywhere while we're getting things going. However, these should be safe,
		this.fetchFromDuringSetup = ['args', 'config', 'environment']

		this.Configure()
		this.RegisterIncludedClasses()
		this.AddArgs()
		this.ResetPlacementSession()


	# Destructors do not work reliably in python.
	# NOTE: you CANNOT delete *this without first Pop()ing it from the ExecutorTracker.
	# def __del__(this):
	# 	ExecutorTracker.Instance().Pop(this)


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

		this.asyncSession = FuturesSession()

	# Add a place to search for SelfRegistering classes.
	# These should all be relative to the invoking working directory (i.e. whatever './' is at time of calling Executor())
	def RegisterDirectory(this, directory):
		this.registerDirectories.append(os.path.abspath(os.path.join(this.cwd,directory)))


	# Global logging config.
	# Override this method to disable or change.
	# This method will add a 'setupBy' member to the root logger in order to ensure no one else (e.g. another Executor) tries to reconfigure the logger while we're using it.
	# The 'setupBy' member will be removed from the root logger by TeardownLogging, which is called in AfterFunction().
	def SetupLogging(this):
		try:
			util.AddLoggingLevel('recovery', logging.ERROR+1)
		except:
			# Could already be setup.
			pass

		class CustomFormatter(logging.Formatter):

			preFormat = util.console.GetColorCode('white', 'dark') + '__TIME__ '
			levelName = '[%(levelname)8s] '
			indentation = util.console.GetColorCode('blue', 'dark', styles=['faint']) + '__INDENTATION__' + util.console.GetColorCode('white', 'dark', styles=['none'])
			message = '%(message)s '
			postFormat = util.console.GetColorCode('white', 'dark') + '(%(filename)s:%(lineno)s)' + util.console.resetStyle

			formats = {
				logging.DEBUG: preFormat + levelName + indentation + util.console.GetColorCode('cyan', 'dark') + message + postFormat,
				logging.INFO: preFormat + levelName + indentation + util.console.GetColorCode('white', 'light') + message + postFormat,
				logging.WARNING: preFormat + levelName + indentation + util.console.GetColorCode('yellow', 'light') + message + postFormat,
				logging.ERROR: preFormat + levelName + indentation + util.console.GetColorCode('red', 'dark') + message + postFormat,
				logging.RECOVERY: preFormat + levelName + indentation + util.console.GetColorCode('green', 'light') + message + postFormat,
				logging.CRITICAL: preFormat + levelName + indentation + util.console.GetColorCode('red', 'light', styles=['bold']) + message + postFormat
			}

			def format(this, record):
				log_fmt = this.formats.get(record.levelno)

				executor = None
				if (hasattr(logging.getLogger(), 'setupBy')):
					executor = getattr(logging.getLogger(), 'setupBy')

					# The executor won't have populated its optionalKWArgs until after this method is effected.
					# So we wait until the last optional arg is set to start using the executor.
					if (not hasattr(executor, 'log_aggregate_url')):
						executor = None

				if (executor):
					# Add indentation.
					if (executor.log_indentation and executor.log_tab_width):
						log_fmt = log_fmt.replace('__INDENTATION__', f"|{' ' * (executor.log_tab_width - 1)}" * (FunctorTracker.GetCount() - 1)) # -1 because we're already in a Functor.
					else:
						log_fmt = log_fmt.replace('__INDENTATION__', ' ')

					# Add time.
					if (executor.log_time_stardate):
						log_fmt = log_fmt.replace('__TIME__', f"{EOT.GetStardate()}")
					else:
						log_fmt = log_fmt.replace('__TIME__', "%(asctime)s")

					# Aggregate logs remotely.
					if (executor.log_aggregate 
						and executor.repo.username is not None 
						and executor.repo.password is not None
						and record.module != 'connectionpool' # Prevent recursion.
						):
						aggregateEndpoint = executor.log_aggregate_url
						log = {
							'level': record.levelname,
							'message': record.getMessage(), # TODO: Sanitize to prevent 400 errors.
							'source': executor.name,
							'timestamp': EOT.GetStardate()
						}
						try:
							executor.asyncSession.put(aggregateEndpoint, json=log, auth=(executor.repo.username, executor.repo.password))
						except Exception as e:
							pass
				else:
					log_fmt = log_fmt.replace('__INDENTATION__', ' ')
					log_fmt = log_fmt.replace('__TIME__', "%(asctime)s")

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
		this.Set('log_file', this.Fetch('log_file', None, this.fetchFromDuringSetup))
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


	# End the current placement session (if any)
	def ResetPlacementSession(this):
		this.placement.session.active = False
		this.placement.session.level = this.placement.max
		this.placement.session.hierarchy = {}
		this.placement.session.current = []
		logging.debug(f"Dependency placement session ended; level is now {this.placement.session.level}")

	# Track to the current location in the placement hierarchy.
	def GetPlacementSessionCurrentPosition(this):
		if (not this.placement.session.active):
			return None
		ret = this.placement.session.hierarchy
		for place in this.placement.session.hierarchy:
			ret = ret[place]
		return ret
	
	def BeginPlacing(this, toPlace):
		if (not this.placement.session.active):
			this.placement.session.active = True
		hierarchy = this.GetPlacementSessionCurrentPosition()
		hierarchy[toPlace] = {}
		this.placement.session.current.append(toPlace)
		this.placement.session.level -= 1
		logging.debug(f"Placing {toPlace}; level is now {this.placement.session.level}")

	# Once the proper location of a Functor has been derived, remove it from the hierarchy.
	# Additionally, if we're the last ones to play with the current session, reset it.
	def ResolvePlacementOf(this, placed):
		if (not this.placement.session.active):
			return
		try:
			this.placement.session.current.remove(placed)
			hierarchy = this.GetPlacementSessionCurrentPosition()
			if (not len(this.placement.session.current)):
				this.ResetPlacementSession()
			elif (hierarchy and placed in hierarchy.keys()):
				del hierarchy[placed]
				this.placement.session.level += 1
			logging.debug(f"Resolved placement of {placed}; level is now {this.placement.session.level}")
		except:
			pass # key errors when getting an existing Functor...
		

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
			'method'
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


	# Grok the configFile and populate this.config
	def ParseConfigFile(this, configFile):
		if (this.configType in ['py']):
			this.RegisterAllClassesInDirectory(Path('./').joinpath('/'.join(this.parsedArgs.config.split['/'][:-1])))
			functor = SelfRegistering(this.parsedArgs.config.split('/')[-1].split('.')[0])
			this.config = functor(executor=this)
		elif (this.configType in ['json', 'yml', 'yaml']):
			# Yaml doesn't allow tabs. We do. Convert.
			this.config = yaml.safe_load(configFile.read().replace('\t', '  '))
		else:
			raise ExecutorSetupError(f"Unknown configuration file type: {this.configType}")


	# Populate the configuration details for *this.
	def PopulateConfig(this):
		this.config = None
		this.configType = None

		if (this.parsedArgs.config is None and this.defaultConfigFile is not None):
			for ext in this.configFileExtensions:
				possibleConfig = f"{this.defaultConfigFile}.{ext}"
				if (Path(possibleConfig).exists()):
					this.parsedArgs.config = possibleConfig
					break

		logging.debug(f"Populating config from {this.parsedArgs.config}")

		if (this.parsedArgs.config is None):
			return

		if (not os.path.isfile(this.parsedArgs.config)):
			logging.error(f"Could not open configuration file: {this.parsedArgs.config}")
			return
		
		this.configType = this.parsedArgs.config.split('.')[-1]

		configFile = open(this.parsedArgs.config, "r")
		this.ParseConfigFile(configFile)
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
	def SetVerbosity(this, fetch=True):
		if (fetch):
			# Take the highest of -v vs --verbosity
			verbosity = this.EvaluateToType(this.Fetch('verbosity', 0, this.fetchFromDuringSetup))
			if (verbosity > this.verbosity):
				logging.debug(f"Setting verbosity to {verbosity}") # debug statements will be available when using external systems, like pytest.
				this.verbosity = verbosity

		if (this.verbosity == 0):
			logging.getLogger().handlers[0].setLevel(logging.CRITICAL)
			logging.getLogger().setLevel(logging.CRITICAL)
		if (this.verbosity == 1):
			logging.getLogger().handlers[0].setLevel(logging.WARNING)
			logging.getLogger().setLevel(logging.WARNING)
		elif (this.verbosity == 2):
			logging.getLogger().handlers[0].setLevel(logging.INFO)
			logging.getLogger().setLevel(logging.INFO)
		elif (this.verbosity >= 3):
			logging.getLogger().handlers[0].setLevel(logging.DEBUG)
			logging.getLogger().setLevel(logging.DEBUG)
			logging.getLogger('urllib3').setLevel(logging.WARNING)
		
		if (this.verbosity >= 5):
			logging.getLogger('urllib3').setLevel(logging.DEBUG)


	# Do the argparse thing.
	# Extra arguments are converted from --this-format to this_format, without preceding dashes. For example, --repo-url ... becomes repo_url ...
	# NOTE: YOU CANNOT USE @recoverable METHODS HERE!
	def ParseArgs(this):
		this.parsedArgs, extraArgs = this.argparser.parse_known_args()

		this.verbosity = this.parsedArgs.verbose

		# If verbosity was specified on the command line, let's print more info while reading in the config, etc.
		this.SetVerbosity(False)

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

		# Track *this globally
		# This needs to be done before the config is populated, in case we use a py file that has External Methods.
		ExecutorTracker.Instance().Push(this)

		this.PopulateConfig()
		this.SetVerbosity()
		this.SetLogFile()
		logging.debug(f"<---- {this.name} (log level: {logging.getLogger().level}) ---->")
		logging.debug(f"Got extra arguments: {this.extraArgs}") # has to be after verbosity setting
		logging.debug(f"Got config contents: {this.config}")
		this.PopulateRepoDetails()
		this.placement.max = this.Fetch('placement_max', 255, this.fetchFromDuringSetup)


	# Functor required method
	# Override this with your own workflow.
	def Function(this):
		
		# NOTE: class registration may instantiate other Executors.
		this.RegisterAllClasses()
		
		this.InitData()


	# By default, Executors do not act on this.next; instead, they make it available to all Executed Functors.
	def CallNext(this):
		pass


	# Close out anything we left open.
	def AfterFunction(this):
		this.TeardownLogging()


	def WarmUpFlow(this, flow):
		flow.WarmUp(executor=this)


	# Flows are domain-like strings which can be resolved to a Functor.
	@recoverable
	def Flow(this, flow):
		logging.debug(f"Calculating flow: {flow}")

		flowList = flow.split('.')
		flowList.reverse()
		current = this.GetRegistered(flowList.pop(0), 'flow')
		while (True):
			this.WarmUpFlow(current)
			if (not len(flowList)):
				break

			current = current.methods[flowList.pop(0)]
		return current()
	

	# Execute a Functor based on name alone (not object).
	# If the given Functor has been Executed before, the cached Functor will be called again. Otherwise, a new Functor will be constructed.
	@recoverable
	def Execute(this, functorName, *args, **kwargs):
		packageType = this.defaultPackageType
		if ('packageType' in kwargs):
			packageType = kwargs.pop('packageType')

		logging.debug(f"Executing {functorName}({', '.join([str(a) for a in args] + [k+'='+str(v) for k,v in kwargs.items()])})")

		if (functorName in this.cachedFunctors):
			return this.cachedFunctors[functorName](*args, **kwargs, executor=this)

		functor = this.GetRegistered(functorName, packageType)
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

		openArchive = ZipFile(packageZipPath, 'r')
		extractLoc = this.repo.store
		if (createSubDirectory):
			extractLoc = os.path.join(extractLoc, packageName)
		elif (this.placement.session.active):
			extractLoc = os.path.join(extractLoc, str(this.placement.session.level))
		logging.debug(f"Extracting {packageZipPath} to {extractLoc}")
		openArchive.extractall(f"{extractLoc}")
		openArchive.close()
		os.remove(packageZipPath)

		if (registerClasses):
			this.RegisterAllClassesInDirectory(this.repo.store)

		return True

	# RETURNS and instance of a Datum, Functor, etc. (aka modules) which has been discovered by a prior call of RegisterAllClassesInDirectory()
	# Will attempt to register existing modules if one of the given name is not found. Failing that, the given package will be downloaded if it can be found online.
	# Both python modules and other eons modules of the same packageType will be installed automatically in order to meet all required dependencies of the given module.
	@recoverable
	def GetRegistered(this,
		registeredName,
		packageType=""):

		try:
			registered = SelfRegistering(registeredName)
		except Exception as e:
			# We couldn't get what was asked for. Let's try asking for help from the error resolution machinery.
			packageName = registeredName
			if (packageType):
				packageName = f"{registeredName}.{packageType}"
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
	def SplitNameOnpackageType(name):
		splitName = name.split('_')
		if (len(splitName)>1):
			return splitName[0], splitName[1]
		return "", name


	# Set a global value for use throughout all python modules.
	def SetGlobal(this, name, value, setFromFetch=False):
		# In cause the value was accessed with ".", we need to cast it to a DotDict.
		if (isinstance(value, dict)):
			value = util.DotDict(value)

		logging.debug(f"Setting global value {name} = {value}")
		setattr(builtins, name, value)
		this.globals.update({name: setFromFetch})


	# Move a value from Fetch to globals.
	def SetGlobalFromFetch(this, name):
		value = None
		isSet = False

		if (not isSet and this.globalContextKey):
			context = this.Fetch(this.globalContextKey)
			if (util.HasAttr(context, name)):
				value =  this.EvaluateToType(util.GetAttr(context, name))
				isSet = True

		if (not isSet):
			logging.debug(f"Fetching {name}...")
			val, fetched = this.FetchWithout(['globals', 'this'], name, start=False)
			if (fetched):
				value = this.EvaluateToType(val)
				isSet = True

		if (isSet):
			this.SetGlobal(name, value)
		else:
			logging.error(f"Failed to set global variable {name}")


	# Remove a variable from python's globals (i.e. builtins module)
	def ExpireGlobal(this, toExpire):
		logging.debug(f"Expiring global {toExpire}")
		try:
			delattr(builtins, toExpire)
		except Exception as e:
			logging.error(f"Failed to expire {toExpire}: {e}")
		# Carry on.


	# Remove all the globals *this has created.
	def ExpireAllGlobals(this):
		for gbl in this.globals.keys():
			this.ExpireGlobal(gbl)


	# Re-Fetch globals but leave manually set globals alone.
	def UpdateAllGlobals(this):
		logging.debug(f"Updating all globals")
		for gbl, fetch in this.globals.items():
			if (fetch):
				this.SetGlobalFromFetch(gbl)


	# Change the context key we use for fetching globals.
	# Then update globals.
	def SetGlobalContextKey(this, contextKey):
		updateGlobals = False
		if (this.globalContextKey != contextKey):
			updateGlobals = True

		logging.debug(f"Setting current config key to {contextKey}")
		this.globalContextKey = contextKey

		if (updateGlobals):
			this.UpdateAllGlobals()


	# Push a sub-context onto the current context
	def PushGlobalContextKey(this, keyToPush):
		this.SetGlobalContextKey(f"{this.globalContextKey}.{keyToPush}")


	# Pop a sub-context from the current context
	# The keyToPop must currently be the last key added.
	def PopGlobalContextKey(this, keyToPop):
		if (not this.globalContextKey.endswith(keyToPop)):
			raise GlobalError(f"{keyToPop} was not the last key pushed. Please pop {this.globalContextKey.split('.')[-1]} first.")
		this.globalContextKey = '.'.join(this.globalContextKey.split('.')[:-1])


	# Uses the ResolveError Functors to process any errors.
	@recoverable
	def ResolveError(this, error, attemptResolution, obj, function):
		if (attemptResolution >= len(this.resolveErrorsWith)):
			raise FailedErrorResolution(f"{this.name} does not have {attemptResolution} resolutions to fix this error: {error} (it has {len(this.resolveErrorsWith)})")

		resolution = this.GetRegistered(this.resolveErrorsWith[attemptResolution], "resolve") # Okay to ResolveErrors for ErrorResolutions.
		this.errorResolutionStack, errorMightBeResolved = resolution(executor=this, error=error, obj=obj, function=function)
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
