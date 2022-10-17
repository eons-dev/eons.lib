import logging
import os
import shutil
from copy import deepcopy
from .Constants import *
from .Datum import Datum
from .Exceptions import *
from .Utils import util
# Don't import Method or Executor, even though they are required: it will cause a circular dependency.
# Instead, pretend there's a forward declaration here and don't think too hard about it ;)
################################################################################

# Functor is a base class for any function-oriented class structure or operation.
# This class derives from Datum, primarily, to give it a name but also to allow it to be stored and manipulated, should you so desire.
# Functors will automatically Fetch any ...Args specified.
# You may additionally specify required methods (per @method()) and required programs (i.e. external binaries).
# When Executing a Functor, you can say 'next=[...]', in which case multiple Functors will be Executed in sequence. This is necessary for the method propagation machinary to work.
# When invoking a sequence of Functors, only the result of the last Functor to be Executed or the first Functor to fail will be returned.
class Functor(Datum):

	def __init__(this, name=INVALID_NAME()):
		super().__init__(name)

		this.initialized = False

		# All necessary args that *this cannot function without.
		this.requiredKWArgs = []

		# Static arguments are Fetched when *this is first called and never again.
		# All static arguments are required.
		this.staticKWArgs = []
		this.staticArgsValid = False

		# Because values can be Fetched from *this, values that should be provided in arguments will be ignored in favor of those Fetched by a previous call to *this.
		# Thus, we can't enable 'this' when Fetching required or optional KWArgs (this is done for you in ValidateArgs)
		# If you want an arg to be populated by a child's member, make it static.

		# For optional args, supply the arg name as well as a default value.
		this.optionalKWArgs = {}

		# Instead of taking ...Args and ...KWArgs, we only take KWArgs.
		# You can list ordered arguments here which will correspond with either required or optional KWArgs.
		# If the arg you specify here does not exist in ...KWArgs, an error will be thrown.
		# Use this to make calling your Functor easier (e.g. MyMethod('some value') vs MyMethod(my_value='some value'))
		this.argMapping = []

		# Default places to Fetch from.
		# Add to this list when extending Fetch().
		# Remove from this list to restrict Fetching behavior.
		# Reorder this list to make Fetch more efficient for your use case.
		# Also see FetchWith and FetchWithout for ease-of-use methods.
		this.fetchFrom = [
			'this',
			'args',
			'config', #local (if applicable) or per Executor; should be before 'executor' if using a local config.
			'precursor',
			'executor',
			'environment',
		]

		# Fetch is modular.
		# You can add your own {'from':this.customSearchMethod} pairs to fetchLocations by overriding PopulateFetchLocations().
		# Alternatively, you may add to fetchLocations automatically by adding a fetchFrom entry and defining a method called f"fetch_location_{your new fetchFrom entry}(this, varName, default)".
		# The order of fetchLocations does not matter; the order of each fetchFrom provided to Fetch() does. This allows users to set their preferred search order for maximum efficiency.
		this.fetchLocations = {}

		# All @methods.
		# See Method.py for details.
		# NOTE: Functor cannot have @methods, since it would create a circular dependency. However, all downstream children of Functor may.
		this.methods = {}

		# You probably don't need to change this.
		# Similar to fetchFrom, methodSources lists where methods should be populated from and in what order
		# Each entry is a key-value pair representing the accessible member (member's members okay) and whether or not to honor Method.propagate.
		# If the value is False, all methods will be added to *this.methods and will overwrite any existing methods. Otherwise, only methods with propagate == True will be added and combined with existing methods. When in doubt, prefer True.
		this.methodSources = {
			'classMethods': False, # classMethods is created when a class uses @method()s
			'precursor.methods': True
		}

		# Specify any methods / member functions you need here.
		# *this will not be invoked unless these methods have been provided by a precursor.
		this.requiredMethods = []

		# All external dependencies *this relies on (binaries that can be found in PATH).
		# These are treated as static args (see above).
		this.requiredPrograms = []

		# For converting config value names.
		# e.g. "type": "projectType" makes it so that when calling Set("projectType", ...),  this.type is changed.
		this.configNameOverrides = {}

		# Rolling back can be disabled by setting this to False.
		this.enableRollback = True

		# Numerical result indication the success or failure of *this.
		# Set automatically.
		# 0 is invalid; 1 is best; higher numbers are usually worse.
		this.result = 0

		# Whether or not we should pass on exceptions when calls fail.
		this.raiseExceptions = True

		# Ease of use members
		# These can be calculated in Function and Rollback, respectively.
		this.functionSucceeded = False
		this.rollbackSucceeded = False

		# That which came before.
		this.precursor = None

		# The progenitor of *this.
		this.executor = None

		# Those which come next (in order).
		this.next = []


	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		pass


	# Undo any changes made by Function.
	# Please override this too!
	def Rollback(this):
		pass


	# Override this to check results of operation and report on status.
	# Override this to perform whatever success checks are necessary.
	def DidFunctionSucceed(this):
		return this.functionSucceeded


	# RETURN whether or not the Rollback was successful.
	# Override this to perform whatever success checks are necessary.
	def DidRollbackSucceed(this):
		return this.rollbackSucceeded


	# Grab any known and necessary args from this.kwargs before any Fetch calls are made.
	def ParseInitialArgs(this):
		pass


	# Override this with any logic you'd like to run at the top of __call__
	def BeforeFunction(this):
		pass


	# Override this with any logic you'd like to run at the bottom of __call__
	def AfterFunction(this):
		pass

	# Create a list of methods / member functions which will search different places for a variable.
	# See the end of the file for examples of these methods.
	def PopulateFetchLocations(this):
		try:
			for loc in this.fetchFrom:
				this.fetchLocations.update({loc:getattr(this,f"fetch_location_{loc}")})
		except:
			# If the user didn't define fetch_location_{loc}(), that's okay. No need to complain
			pass


	# Convert Fetched values to their proper type.
	# This can also allow for use of {this.val} expression evaluation.
	# If evaluateExpressions is True, this will automatically evaluate any strings containing {} expressions.
	def EvaluateToType(this, value, evaluateExpressions=True):
		if (value is None or value == "None"):
			return None

		if (isinstance(value, (bool, int, float))):
			return value

		if (isinstance(value, dict)):
			ret = {}
			for key, value in value.items():
				ret[key] = this.EvaluateToType(value)
			return ret

		if (isinstance(value, list)):
			ret = []
			for value in value:
				ret.append(this.EvaluateToType(value))
			return ret

		if (isinstance(value, str)):
			# Automatically determine if the string is an expression.
			# If it is, evaluate it.
			if (evaluateExpressions and ('{' in value and '}' in value)):
				evaluatedValue = eval(f"f\"{value}\"")
			else:
				evaluatedValue = value

			# Check resulting type and return a casted value.
			# TODO: is there a better way than double cast + comparison?
			if (evaluatedValue.lower() == "false"):
				return False
			elif (evaluatedValue.lower() == "true"):
				return True

			try:
				if (str(float(evaluatedValue)) == evaluatedValue):
					return float(evaluatedValue)
			except:
				pass

			try:
				if (str(int(evaluatedValue)) == evaluatedValue):
					return int(evaluatedValue)
			except:
				pass

			# The type must be a plain-old string.
			return evaluatedValue

		# Meh. Who knows?
		return value


	# Wrapper around setattr
	def Set(this, varName, value, evaluateExpressions=True):
		value = this.EvaluateToType(value, evaluateExpressions)
		for key, var in this.configNameOverrides.items():
			if (varName == key):
				varName = var
				break
		logging.debug(f"Setting ({type(value)}) {varName} = {value}")
		setattr(this, varName, value)


	# Will try to get a value for the given varName from:
	#	first: this
	#	second: whatever was called before *this
	#	third: the executor (args > config > environment)
	# RETURNS:
	#   When starting: the value of the given variable or default
	#   When not starting (i.e. when called from another Fetch() call): a tuple containing either the value of the given variable or default and a boolean indicating if the given value is the default or if the Fetch was successful.
	# The attempted argument will keep track of where we've looked so that we don't enter any cycles. Attempted implies not start.
	def Fetch(this, varName, default=None, fetchFrom=None, start=True, attempted=None):
		if (attempted is None):
			attempted = []

		if (this.name in attempted):
			logging.debug(f"...{this.name} detected loop ({attempted}) while trying to fetch {varName}; using default: {default}.")
			if (start):
				return default
			else:
				return default, False

		attempted.append(this.name)

		if (fetchFrom is None):
			fetchFrom = this.fetchFrom

		if (start):
			logging.debug(f"Fetching {varName} from {fetchFrom}...")

		for loc in fetchFrom:
			if (loc not in this.fetchLocations.keys()):
				# Maybe the location is meant for executor, precursor, etc.
				continue

			ret, found = this.fetchLocations[loc](varName, default, fetchFrom, attempted)
			if (found):
				logging.debug(f"...{this.name} got {varName} from {loc}.")
				if (start):
					return ret
				return ret, True

		if (start):
			logging.debug(f"...{this.name} could not find {varName}; using default: {default}.")
			return default
		else:
			return default, False


	# Ease of use method for Fetching while including certain search locations.
	def FetchWith(this, doFetchFrom, varName, default=None, currentFetchFrom=None, start=True, attempted=None):
		if (currentFetchFrom is None):
			currentFetchFrom = this.fetchFrom
		fetchFrom = list(set(currentFetchFrom + doFetchFrom))
		return this.Fetch(varName, default, fetchFrom, start, attempted)

	# Ease of use method for Fetching while excluding certain search locations.
	def FetchWithout(this, dontFetchFrom, varName, default=None, currentFetchFrom=None, start=True, attempted=None):
		if (currentFetchFrom is None):
			currentFetchFrom = this.fetchFrom
		fetchFrom = [f for f in this.fetchFrom if f not in dontFetchFrom]
		return this.Fetch(varName, default, fetchFrom, start, attempted)

	# Ease of use method for Fetching while including some search location and excluding others.
	def FetchWithAndWithout(this, doFetchFrom, dontFetchFrom, varName, default=None, currentFetchFrom=None, start=True, attempted=None):
		if (currentFetchFrom is None):
			currentFetchFrom = this.fetchFrom
		fetchFrom = [f for f in this.fetchFrom if f not in dontFetchFrom]
		fetchFrom = list(set(fetchFrom + doFetchFrom))
		return this.Fetch(varName, default, fetchFrom, start, attempted)


	# Make sure arguments are not duplicated.
	# This prefers optional args to required args.
	def RemoveDuplicateArgs(this):
		deduplicate = [
			'requiredKWArgs',
			'requiredMethods',
			'requiredPrograms'
		]
		for dedup in deduplicate:
			setattr(this, dedup, list(dict.fromkeys(getattr(this, dedup))))

		for arg in this.requiredKWArgs:
			if (arg in this.optionalKWArgs.keys()):
				logging.warning(f"Making required kwarg optional to remove duplicate: {arg}")
				this.requiredKWArgs.remove(arg)


	# Populate all static details of *this.
	def Initialize(this):
		if (this.initialized):
			return

		this.PopulateFetchLocations()
		this.RemoveDuplicateArgs()

		for prog in this.requiredPrograms:
			if (shutil.which(prog) is None):
				raise FunctorError(f"{prog} required but not found in path.")

		this.initialized = True

	# Make sure all static args are valid.
	def ValidateStaticArgs(this):
		if (this.staticArgsValid):
			return

		for skw in this.staticKWArgs:
			if (hasattr(this, skw)): # only in the case of children.
				continue

			fetched = this.Fetch(skw)
			if (fetched is not None):
				this.Set(skw, fetched)
				continue

			# Nope. Failed.
			raise MissingArgumentError(f"Static key-word argument {skw} could not be Fetched.")

		this.staticArgsValid = True


	# Pull all propagating precursor methods into *this.
	# DO NOT USE Fetch() IN THIS METHOD!
	def PopulateMethods(this):

		# In order for this to work properly, each method needs to be a distinct object; hence the need for deepcopy.
		# In the future, we might be able to find a way to share code objects between Functors. However, for now we will allow each Functor to modify its classmethods as it pleases.

		# We have to use util.___Attr() because some sources might have '.'s in them.

		for source, honorPropagate in this.methodSources.items():
			if (not util.HasAttr(this, source)):
				continue
			for method in util.GetAttr(this, source).values():
				if (honorPropagate and not method.propagate):
					continue
				if (method.name in this.methods.keys() and honorPropagate):
					existingMethod = this.methods[method.name]
					if (not existingMethod.inheritMethods):
						continue

					methodToInsert = deepcopy(method)

					if (existingMethod.inheritedMethodsFirst):
						logging.debug(f"Will call {method.name} from {source} to prior to this.")
						methodToInsert.next.append(this.methods[method.name])
						this.methods[method.name] = methodToInsert
					else:
						logging.debug(f"Appending {method.name} from {source} to this.")
						this.methods[method.name].next.append(methodToInsert)
				else:
					this.methods[method.name] = deepcopy(method)

		for method in this.methods.values():
			logging.debug(f"Populating method {this.name}.{method.name}({', '.join([a for a in method.requiredKWArgs] + [a+'='+str(v) for a,v in method.optionalKWArgs.items()])})")
			method.object = this
			setattr(this, method.name, method.__call__.__get__(this, this.__class__)) #...


	# Set this.precursor
	# Also set this.executor because it's easy.
	def PopulatePrecursor(this):
		if (this.executor is None):
			if ('executor' in this.kwargs):
				this.executor = this.kwargs.pop('executor')
			else:
				logging.warning(f"{this.name} was not given an 'executor'. Some features will not be available.")

			if ('precursor' in this.kwargs):
				this.precursor = this.kwargs.pop('precursor')
				logging.debug(f"{this.name} was preceded by {this.precursor.name}")
			else:
				this.precursor = None
				logging.debug(f"{this.name} was preceded by None")


	# Override this with any additional argument validation you need.
	# This is called before BeforeFunction(), below.
	def ValidateArgs(this):
		# logging.debug(f"this.kwargs: {this.kwargs}")
		# logging.debug(f"required this.kwargs: {this.requiredKWArgs}")

		if (len(this.args) > len(this.argMapping)):
			raise MissingArgumentError(f"Too many arguments. Got ({len(this.args)}) {this.args} but expected at most ({len(this.argMapping)}) {this.argMapping}")
		argMap = dict(zip(this.argMapping[:len(this.args)], this.args))
		logging.debug(f"Setting values from args: {argMap}")
		for arg, value in argMap.items():
			this.Set(arg, value)

		#NOTE: In order for *this to be called multiple times, required and optional kwargs must always be fetched and not use stale data from *this.

		if (this.requiredKWArgs):
			for rkw in this.requiredKWArgs:
				if (rkw in argMap.keys()):
					continue

				fetched = this.FetchWithout(['this'], rkw)
				if (fetched is not None):
					this.Set(rkw, fetched)
					continue

				# Nope. Failed.
				logging.error(f"{rkw} required but not found.")
				raise MissingArgumentError(f"Key-word argument {rkw} could not be Fetched.")

		if (this.optionalKWArgs):
			for okw, default in this.optionalKWArgs.items():
				if (okw in argMap.keys()):
					continue

				this.Set(okw, this.FetchWithout(['this'], okw, default=default))

	# When Fetching what to do next, everything is valid EXCEPT the environment. Otherwise, we could do something like `export next='nop'` and never quit.
	# A similar situation arises when using the global config for each Functor. We only use the global config if *this has no precursor.
	def PopulateNext(this):
		dontFetchFrom = [
			'this',
			'environment',
			'executor'
		]
		this.Set('next', this.FetchWithout(dontFetchFrom, 'next', []))


	# Make sure that precursors have provided all necessary methods for *this.
	# NOTE: these should not be static nor cached, as calling something else before *this will change the behavior of *this.
	def ValidateMethods(this):
		for method in this.requiredMethods:
			if (hasattr(this, method) and callable(getattr(this, method))):
				continue

			raise MissingMethodError(f"{this.name} has no method: {method}")


	# RETURNS whether or not we should trigger the next Functor.
	# Override this to add in whatever checks you need.
	def ValidateNext(this, next):
		return True


	# Hook for whatever logic you'd like to run before the next Functor is called.
	def PrepareNext(this, next):
		pass


	# Call the next Functor.
	# RETURN the result of the next Functor or None.
	def CallNext(this):
		if (not this.next):
			return None

		if (this.GetExecutor() is None):
			logging.warning(f"{this.name} has no executor and cannot execute next ({this.next}).")

		next = this.next.pop(0)
		if (not this.ValidateNext(next)):
			raise InvalidNext(f"Failed to validate {next}")
		return this.GetExecutor().Execute(next, precursor=this, next=this.next)


	# Make functor.
	# Don't worry about this; logic is abstracted to Function
	def __call__(this, *args, **kwargs) :
		logging.debug(f"<---- {this.name} ---->")

		this.args = args
		this.kwargs = kwargs

		logging.debug(f"{this.name}({this.args}, {this.kwargs})")

		ret = None
		nextRet = None
		try:
			this.PopulatePrecursor()
			this.Initialize() # nop on call 2+
			this.PopulateMethods() # Doesn't require Fetch; depends on precursor
			this.ParseInitialArgs() # Usually where config is read in.
			this.ValidateStaticArgs() # nop on call 2+
			this.ValidateArgs()
			this.PopulateNext()
			this.ValidateMethods()

			this.BeforeFunction()

			ret = this.Function()

			if (this.DidFunctionSucceed()):
					this.result = 1
					# logging.info(f"{this.name} successful!")
					nextRet = this.CallNext()
			elif (this.enableRollback):
				logging.warning(f"{this.name} failed. Attempting Rollback...")
				this.Rollback()
				if (this.DidRollbackSucceed()):
					this.result = 2
					# logging.info(f"Rollback succeeded. All is well.")
					nextRet = this.CallNext()
				else:
					this.result = 3
					logging.error(f"Rollback FAILED! SYSTEM STATE UNKNOWN!!!")
			else:
				this.result = 4
				logging.error(f"{this.name} failed.")

			this.AfterFunction()

		except Exception as e:
			if (this.raiseExceptions):
				raise e
			else:
				logging.error(f"ERROR: {e}")
				util.LogStack()

		if (this.raiseExceptions and this.result > 2):
			raise FunctorError(f"{this.name} failed with result {this.result}")

		logging.debug(f">---- {this.name} complete ----<")
		if (nextRet is not None):
			return nextRet
		else:
			return ret


	# Adapter for @recoverable.
	# See Recoverable.py for details
	def GetExecutor(this):
		return this.executor


	######## START: Fetch Locations ########

	def fetch_location_this(this, varName, default, fetchFrom, attempted):
		if (hasattr(this, varName)):
			return getattr(this, varName), True
		return default, False


	def fetch_location_precursor(this, varName, default, fetchFrom, attempted):
		if (this.precursor is None):
			return default, False
		return this.precursor.FetchWithAndWithout(['this'], ['environment'], varName, default, fetchFrom, False, attempted)


	def fetch_location_args(this, varName, default, fetchFrom, attempted):

		# this.args can't be searched.

		for key, val in this.kwargs.items():
			if (key == varName):
				return val, True
		return default, False


	# Call the Executor's Fetch method.
	# Exclude 'environment' because we can check that ourselves.
	def fetch_location_executor(this, varName, default, fetchFrom, attempted):
		return this.GetExecutor().FetchWithout(['environment'], varName, default, fetchFrom, False, attempted)


	#NOTE: There is no config in the default Functor. This is done for the convenience of children.
	def fetch_location_config(this, varName, default, fetchFrom, attempted):
		if (not hasattr(this, 'config') or this.config is None):
			return default, False

		for key, val in this.config.items():
			if (key == varName):
				return val, True

		return default, False


	def fetch_location_environment(this, varName, default, fetchFrom, attempted):
		envVar = os.getenv(varName)
		if (envVar is not None):
			return envVar, True
		return default, False

	######## END: Fetch Locations ########
