import logging
import os
import shutil
import dis, inspect
import types
from copy import deepcopy, copy
import builtins
from .Constants import *
from .SelfRegistering import SelfRegistering
from .Datum import Datum
from .BackwardsCompatible import BackwardsCompatible
from .Exceptions import *
from .Utils import util
from .FunctorTracker import FunctorTracker
from .ExecutorTracker import ExecutorTracker
from .Recoverable import Recover

# Don't import Method or Executor, even though they are required: it will cause a circular dependency.
# Instead, pretend there's a forward declaration here and don't think too hard about it ;)
################################################################################

# Functor is a base class for any function-oriented class structure or operation.
# This class derives from Datum, primarily, to give it a name but also to allow it to be stored and manipulated, should you so desire.
# Functors will automatically Fetch any ...Args specified.
# You may additionally specify required methods (per @method()) and required programs (i.e. external binaries).
# When Executing a Functor, you can say 'next=[...]', in which case multiple Functors will be Executed in sequence. This is necessary for the method propagation machinery to work.
# When invoking a sequence of Functors, only the result of the last Functor to be Executed or the first Functor to fail will be returned.
class Functor(Datum, BackwardsCompatible):

	# Which function should be overridden when creating a @kind from *this.
	primaryFunctionName = 'Function'

	def __init__(this, name=INVALID_NAME()):
		Datum.__init__(this, name)
		BackwardsCompatible.__init__(this)

		# All @methods.
		# See Method.py for details.
		# NOTE: Functor cannot have @methods, since it would create a circular dependency. However, all downstream children of Functor may.
		this.methods = {}

		# Settings for the methods of *this
		this.method = util.DotDict()

		# Which method to call when executing *this through __call__.
		this.method.function = 'Function'
		this.method.rollback = 'Rollback'
		
		# You probably don't need to change this.
		# Similar to fetchFrom, methodSources lists where methods should be populated from and in what order
		# Each entry is a key-value pair representing the accessible member (member's members okay) and whether or not to honor Method.propagate.
		# If the value is False, all methods will be added to *this.methods and will overwrite any existing methods. Otherwise, only methods with propagate == True will be added and combined with existing methods. When in doubt, prefer True.
		this.method.sources = {
			'classMethods': False, # classMethods is created when a class uses @method()s
			'precursor.methods': True
		}

		# Specify any methods / member functions you need here.
		# *this will not be invoked unless these methods have been provided by a precursor.
		this.method.required = []

		# Internal var indicating whether or not Initialize has been called.
		this.initialized = False

		# Internal variable used to cache wether WarmUp has been called or not.
		this.warm = False

		# The arguments provided to *this.
		this.args = []
		this.kwargs = {}

		# The arguments *this takes.
		this.arg = util.DotDict()
		this.arg.kw = util.DotDict()

		# All necessary args that *this cannot function without.
		this.arg.kw.required = []

		# Static arguments are Fetched when *this is first called and never again.
		# All static arguments are required.
		this.arg.kw.static = []

		# Mark args that meet the given requirements as valid.
		# For now, only static args require a member variable.
		this.arg.valid = util.DotDict()
		this.arg.valid.static = False

		# Because values can be Fetched from *this, values that should be provided in arguments will be ignored in favor of those Fetched by a previous call to *this.
		# Thus, we can't enable 'this' when Fetching required or optional KWArgs (this is done for you in ValidateArgs)
		# If you want an arg to be populated by a child's member, make it static.

		# For optional args, supply the arg name as well as a default value.
		this.arg.kw.optional = {}

		# Instead of taking ...Args and ...KWArgs, we only take KWArgs.
		# You can list ordered arguments here which will correspond with either required or optional KWArgs.
		# If the arg you specify here does not exist in ...KWArgs, an error will be thrown.
		# Use this to make calling your Functor easier (e.g. MyMethod('some value') vs MyMethod(my_value='some value'))
		this.arg.mapping = []

		# If you'd like to enforce types on your arguments, rather than use Python autotyping, specify the {'argName': type} pairs here.
		this.arg.type = {}

		# Settings for dependency injection.
		this.fetch = util.DotDict()

		# Default places to Fetch from.
		# Add to this list when extending Fetch().
		# Remove from this list to restrict Fetching behavior.
		# Reorder this list to make Fetch more efficient for your use case.
		# Also see FetchWith and FetchWithout for ease-of-use methods.
		this.fetch.use = [
			'this',
			'args',
			'globals',
			'config', #local (if applicable) or per Executor; should be before 'executor' if using a local config.
			'epidef',
			'precursor',
			'caller',
			'executor',
			'environment',
		]


		this.fetch.attr = util.DotDict()

		# fetch.attr.use is used within __getattr__ iff the attribute sought is not found in *this.
		# By editing this list, you can change what values are available to *this using the standard dot notation.
		# Primarily, this method enables sequential Functors to access their precursor's attributes transparently.
		# For example, if, instead of using this.methods, you set a function pointer as a member of a Functor, you can access that function pointer from the next Functor in the sequence (e.g. has_desired_members/can_access.desired_members)
		this.fetch.attr.use = [
			'precursor'
		]

		# Fetch is modular.
		# You can add your own {'from':this.customSearchMethod} pairs to fetchLocations by overriding PopulateFetchLocations().
		# Alternatively, you may add to fetchLocations automatically by adding a fetchFrom entry and defining a method called f"fetch_location_{your new fetchFrom entry}(this, varName, default)".
		# The order of fetchLocations does not matter; the order of each fetchFrom provided to Fetch() does. This allows users to set their preferred search order for maximum efficiency.
		this.fetch.locations = {}

		# System executables that *this depends on.
		this.program = util.DotDict()

		# All external dependencies *this relies on (binaries that can be found in PATH).
		# These are treated as static args (see above).
		this.program.required = []

		# New style overrides.
		this.override = util.DotDict()
		this.override.config = {}

		# Feature flags.
		# What can *this do?
		this.feature = util.DotDict()
		
		# Automatically return this.
		# Also enables partial function calls.
		this.feature.autoReturn = True

		# Rolling back can be disabled by setting this to False.
		this.feature.rollback = True

		# Whether or not we should pass on exceptions when calls fail.
		this.feature.raiseExceptions = True

		# Whether or not to utilize arg.mapping
		# Set to False if you want to capture args as variadic, etc.
		this.feature.mapArgs = True

		# Functors should be tracked by default.
		# Not tracking a Functor means losing access to features like sequencing and the caller member.
		# However, if you have an intermediate layer between your Functors of interest (e.g. EXEC in Elderlang), you may consider disabling tracking of those intermediates.
		# NOTE: The track feature MUST be enabled in order for *this to participate in sequences.
		this.feature.track = True

		# Functors marked as sequential can engage in sequences.
		# Setting this feature to False will prevent the Functor from participating in a sequence.
		# You'll want to set this to False if you intend to override the __truediv__ operator for your Functor.
		# NOTE: This will not have much use if the track feature is disabled.
		this.feature.sequential = True

		this.feature.sequence = util.DotDict()

		# Sequences can clone the proceeding Functors.
		# You'd want to enable this if you plan to make significant modifications to the object provided to PrepareNext(...).
		this.feature.sequence.clone = False

		# If *this stays warm, it will not need to WarmUp() before each call.
		# This essentially results in caching the args and state of *this, and transfers the responsibility of calling WarmUp to the greater system.
		this.feature.stayWarm = False

		# Allow partial function calls by marking *this as incomplete.
		# Incomplete means that more arguments need to be provided.
		this.incomplete = False

		# this.result encompasses the return value of *this.
		# The code is a numerical result indication the success or failure of *this and is set automatically.
		# 0 is success; 1 is no change; higher numbers are some kind of error.
		# this.result.data should be set manually.
		# It is highly recommended that you check result.data in DidFunctionSucceed().
		this.result = util.DotDict()
		this.result.code = 0
		this.result.data = util.DotDict()

		# Ease of use members
		# These can be calculated in Function and Rollback, respectively.
		# Assume success to reduce the overhead of creating small Functors.
		this.functionSucceeded = True
		this.rollbackSucceeded = True

		# That which came before.
		this.precursor = None

		# The reason *this is being __call__()ed.
		# i.e. the previous Functor in the call stack.
		this.caller = None

		# The object to which this belongs.
		# epidef as in "above definition"
		# For example, if *this is a method of another Functor, this.upper would refer to that other Functor.
		this.epidef = None

		# The overarching program manager.
		this.executor = None

		# Those which come next (in order).
		this.next = []

		# Callback method
		this.callback = util.DotDict()
		this.callback.fetch = None

		this.abort = util.DotDict()
		this.abort.WarmUp = False
		this.abort.CallNext = False

		this.cloning = util.DotDict()
		this.cloning.exclusions = [
			'executor',
			'precursor',
			'epidef',
			'caller',
			'next',
			'callback',
			'warm',
		]

		# Mappings to support older versions
		this.MaintainCompatibilityFor(2.0, {
			'method.call': 'callMethod',
			'method.rollback': 'rollbackMethod',
			'method.sources': 'methodSources',
			'method.required': 'requiredMethods',
			'arg.kw.required': 'requiredKWArgs',
			'arg.kw.optional': 'optionalKWArgs',
			'arg.kw.static': 'staticKWArgs',
			'arg.valid.static': 'staticArgsValid',
			'arg.mapping': 'argMapping',
			'fetch.use': 'fetchFrom',
			'fetch.locations': 'fetchLocations',
			'program.required': 'requiredPrograms',
			'override.config': 'configNameOverrides',
			'feature.autoReturn': 'enableAutoReturn',
			'feature.rollback': 'enableRollback',
			'feature.raiseExceptions': 'raiseExceptions',
		})


	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		pass


	# Undo any changes made by Function.
	# Please override this too!
	def Rollback(this):
		pass


	# Return whether or not Function was successful.
	# Override this to perform whatever success and failure checks are necessary.
	def DidFunctionSucceed(this):
		return this.functionSucceeded


	# RETURN whether or not the Rollback was successful.
	# Override this to perform whatever success and failure checks are necessary.
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


	# Override this with any logic you'd like to run at the top of __call__
	def BeforeRollback(this):
		pass


	# Override this with any logic you'd like to run at the bottom of __call__
	def AfterRollback(this):
		pass


	# Called during initialization.
	# Use this to address any type conversion, etc.
	def SupportBackwardsCompatibility(this):
		pass


	# Create a list of methods / member functions which will search different places for a variable.
	# See the end of the file for examples of these methods.
	def PopulateFetchLocations(this):
		try:
			for loc in this.fetch.use:
				this.fetch.locations.update({loc:getattr(this,f"fetch_location_{loc}")})
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
			ret = util.DotDict()
			for key, val in value.items():
				ret[key] = this.EvaluateToType(val, evaluateExpressions)
			return ret

		if (isinstance(value, list)):
			ret = []
			for val in value:
				ret.append(this.EvaluateToType(val, evaluateExpressions))
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
		for key, var in this.override.config.items():
			if (varName == key):
				varName = var
				break
		if (varName in this.arg.type.keys()):
			cls = this.arg.type[varName]
			if (not inspect.isclass(cls) and isinstance(cls, object)):
				cls = cls.__class__
			if (issubclass(cls, Functor)):
				value = cls(value=value)
			else:
				value = cls(value)
		else:
			value = this.EvaluateToType(value, evaluateExpressions)

		logging.info(f"{varName} = {value} ({type(value)})")
		exec(f"this.{varName} = value")


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

		if (this in attempted):
			logging.debug(f"...{this} detected loop ({attempted}) while trying to fetch {varName}; using default: {default}.")
			if (start):
				return default
			else:
				return default, False

		attempted.append(this)

		if (fetchFrom is None):
			fetchFrom = this.fetch.use

		if (start):
			logging.debug(f"Fetching {varName} from {fetchFrom}...")

		for loc in fetchFrom:
			if (loc not in this.fetch.locations.keys()):
				# Maybe the location is meant for executor, precursor, etc.
				continue

			ret, found = this.fetch.locations[loc](varName, default, fetchFrom, attempted)
			if (found):
				logging.debug(f"...{this.name} got {varName} from {loc}.")
				if (this.callback.fetch):
					this.callback.fetch(varName = varName, location = loc, value = ret)
				if (start):
					return ret
				return ret, True

		if (this.callback.fetch):
			this.callback.fetch(varName = varName, location = 'default', value = default)

		if (start):
			logging.debug(f"...{this.name} could not find {varName}; using default: {default}.")
			return default
		else:
			return default, False


	# Ease of use method for Fetching while including certain search locations.
	def FetchWith(this, doFetchFrom, varName, default=None, currentFetchFrom=None, start=True, attempted=None):
		if (currentFetchFrom is None):
			currentFetchFrom = this.fetch.use
		fetchFrom = list(set(currentFetchFrom + doFetchFrom))
		return this.Fetch(varName, default, fetchFrom, start, attempted)

	# Ease of use method for Fetching while excluding certain search locations.
	def FetchWithout(this, dontFetchFrom, varName, default=None, currentFetchFrom=None, start=True, attempted=None):
		if (currentFetchFrom is None):
			currentFetchFrom = this.fetch.use
		fetchFrom = [f for f in this.fetch.use if f not in dontFetchFrom]
		return this.Fetch(varName, default, fetchFrom, start, attempted)

	# Ease of use method for Fetching while including some search location and excluding others.
	def FetchWithAndWithout(this, doFetchFrom, dontFetchFrom, varName, default=None, currentFetchFrom=None, start=True, attempted=None):
		if (currentFetchFrom is None):
			currentFetchFrom = this.fetch.use
		fetchFrom = [f for f in this.fetch.use if f not in dontFetchFrom]
		fetchFrom = list(set(fetchFrom + doFetchFrom))
		return this.Fetch(varName, default, fetchFrom, start, attempted)


	# Make sure arguments are not duplicated.
	# This prefers optional args to required args.
	def RemoveDuplicateArgs(this):
		deduplicate = [
			'arg.kw.required',
			'method.required',
			'program.required'
		]
		for dedup in deduplicate:
			exec(f"this.{dedup} = list(dict.fromkeys(this.{dedup}))")

		for arg in this.arg.kw.required:
			if (arg in this.arg.kw.optional.keys()):
				logging.warning(f"Making required kwarg optional to remove duplicate: {arg}")
				this.arg.kw.required.remove(arg)


	# Populate all static details of *this.
	def Initialize(this):
		if (this.initialized):
			return
		
		this.SupportBackwardsCompatibility()

		this.PopulateFetchLocations()
		this.RemoveDuplicateArgs()

		for prog in this.program.required:
			if (shutil.which(prog) is None):
				raise FunctorError(f"{prog} required but not found in path.")

		this.initialized = True

	# Make sure all static args are valid.
	def ValidateStaticArgs(this):
		if (this.arg.valid.static):
			return

		for skw in this.arg.kw.static:
			if (util.HasAttr(this, skw)): # only in the case of children.
				continue

			fetched = this.Fetch(skw)
			if (fetched is not None):
				this.Set(skw, fetched)
				continue

			# Nope. Failed.
			raise MissingArgumentError(f"Static key-word argument {skw} could not be Fetched.")

		this.arg.valid.static = True


	# Pull all propagating precursor methods into *this.
	# DO NOT USE Fetch() IN THIS METHOD!
	def PopulateMethods(this):

		# In order for this to work properly, each method needs to be a distinct object; hence the need for deepcopy.
		# In the future, we might be able to find a way to share code objects between Functors. However, for now we will allow each Functor to modify its classmethods as it pleases.

		# We have to use util.___Attr() because some sources might have '.'s in them.

		for source, honorPropagate in this.method.sources.items():
			if (not util.HasAttr(this, source)):
				logging.debug(f"Could not find {source}; will not pull in its methods.")
				continue

			methodSource = util.GetAttr(this, source)
			if (not isinstance(methodSource, dict)):
				logging.debug(f"{source} is not a dict; will not pull in its methods.")
				continue

			logging.debug(f"Populating methods from {source}.")
			for method in methodSource.values():
				if (honorPropagate and not method.propagate):
					continue
				if (method.name in this.methods.keys() and honorPropagate):
					existingMethod = this.methods[method.name]
					if (not existingMethod.inheritMethods):
						continue

					methodToInsert = deepcopy(method)
					methodToInsert.epidef = this
					methodToInsert.UpdateSource()

					if (existingMethod.inheritedMethodsFirst):
						logging.debug(f"Will call {method.name} from {source} to prior to this.")
						methodToInsert.next.append(this.methods[method.name])
						this.methods[method.name] = methodToInsert
					else:
						logging.debug(f"Appending {method.name} from {source} to this.")
						this.methods[method.name].next.append(methodToInsert)
				else:
					this.methods[method.name] = deepcopy(method)
					this.methods[method.name].epidef = this
					this.methods[method.name].UpdateSource()

		for method in this.methods.values():
			logging.debug(f"Populating method {this.name}.{method.name}({', '.join([a for a in method.arg.kw.required] + [a+'='+str(v) for a,v in method.arg.kw.optional.items()])})")

			# Python < 3.11
			# setattr(this, method.name, method.__call__.__get__(this, this.__class__))

			# appears to work for all python versions >= 3.8
			# setattr(this, method.name, method.__call__.__get__(method, method.__class__))
			
			setattr(this, method.name, types.MethodType(method, this))


	# Set this.precursor
	# Also set this.executor because it's easy.
	def PopulatePrecursor(this):
		if (this.executor is None):
			if ('executor' in this.kwargs):
				this.executor = this.kwargs.pop('executor')
			else:
				this.executor = ExecutorTracker.GetLatest()
		if (not this.executor):
			logging.warning(f"{this.name} was not given an 'executor'. Some features will not be available.")

		if ('precursor' in this.kwargs and this.kwargs['precursor'] is not None):
			this.Set('precursor', this.kwargs.pop('precursor'))
		else:
			this.Set('precursor', None)


	# Override this with any additional argument validation you need.
	# This is called before BeforeFunction(), below.
	def ValidateArgs(this):
		# logging.debug(f"this.kwargs: {this.kwargs}")
		# logging.debug(f"required this.kwargs: {this.arg.kw.required}")

		if (this.feature.mapArgs):
			if (len(this.args) > len(this.arg.mapping)):
				raise MissingArgumentError(f"{this.name} called with too many arguments. Got ({len(this.args)}) {this.args} but expected at most ({len(this.arg.mapping)}) {this.arg.mapping}")
			argMap = dict(zip(this.arg.mapping[:len(this.args)], this.args))
			logging.debug(f"Setting values from args: {argMap}")
			for arg, value in argMap.items():
				this.Set(arg, value)

		#NOTE: In order for *this to be called multiple times, required and optional kwargs must always be fetched and not use stale data from *this.

		if (this.arg.kw.required):
			for rkw in this.arg.kw.required:
				if (this.feature.mapArgs):
					if (rkw in argMap.keys()):
						continue
				
				logging.debug(f"Fetching required value {rkw}...")
				fetched, found = this.FetchWithout(['this'], rkw, start = False)
				if (found):
					this.Set(rkw, fetched)
					continue

				# Nope. Failed.
				logging.error(f"{rkw} required but not found.")
				raise MissingArgumentError(f"Key-word argument {rkw} could not be Fetched.")

		if (this.arg.kw.optional):
			for okw, default in this.arg.kw.optional.items():
				if (this.feature.mapArgs):
					if (okw in argMap.keys()):
						continue

				this.Set(okw, this.FetchWithout(['this'], okw, default=default))

	# When Fetching what to do next, everything is valid EXCEPT the environment. Otherwise, we could do something like `export next='nop'` and never quit.
	# A similar situation arises when using the global config for each Functor. We only use the global config if *this has no precursor.
	def PopulateNext(this):
		dontFetchFrom = [
			'this',
			'environment',
			'executor',
			'globals'
		]
		# Let 'next' evaluate its expressions if it chooses to. We don't need to do that pre-emptively.
		this.Set('next', this.FetchWithout(dontFetchFrom, 'next', []), evaluateExpressions=False)


	# Make sure that precursors have provided all necessary methods for *this.
	# NOTE: these should not be static nor cached, as calling something else before *this will change the behavior of *this.
	def ValidateMethods(this):
		for method in this.method.required:
			if (util.HasAttr(this, method) and callable(util.GetAttr(this, method))):
				continue

			raise MissingMethodError(f"{this.name} has no method: {method}")


	# Hook for whatever logic you'd like to run before the next Functor is called.
	# ValidateNext will be called AFTER PrepareNext, so you don't need to make any readiness checks here.
	# NOTE: if *this has feature.sequence.clone enabled, this method will be passed a cloned Functor, so you are more than welcome to make even destructive changes to it.
	def PrepareNext(this, next):
		# next.feature.autoReturn = True # <- recommended if you'd like to be able to access the modified sequence result.
		pass


	# RETURNS whether or not we should trigger the next Functor.
	# Override this to add in whatever checks you need.
	# PrepareNext will be called BEFORE ValidateNext, so you don't need to make any preparations here.
	# NOTE: you may silently invalidate the next Functor by setting this.abort.CallNext = True and returning True.
	def ValidateNext(this, next):
		return True


	# Call the next Functor.
	# This will clone the next Functor before it's executed. This is to prevent any changes made to the next Functor from persisting.
	# RETURN the result of the next Functor or None.
	def CallNext(this):
		# TODO: Why would next ever not be a list This should be the same as the FIXME below.s
		if (not this.next or not isinstance(this.next, list) or len(this.next) == 0):
			return None
		
		
		# Something odd happens here; we've been getting:
		# AttributeError("'builtin_function_or_method' object has no attribute 'pop'")
		# But that implies we're getting a valid next object that is not a list.
		# FIXME: Debug this.
		proceedToNext = False

		# Something odd happens here; we've been getting:
		# AttributeError("'builtin_function_or_method' object has no attribute 'pop'")
		# But that implies we're getting a valid next object that is not a list.
		# FIXME: Debug this.
		proceedToNext = False
		next = None
		nextName = ""
		try:
			next = this.next.pop(0)
			if (isinstance(next, str)):
				nextName = next
				if (this.GetExecutor()):
					next = this.GetExecutor().GetRegistered(next)
				else:
					next = SelfRegistering(nextName)
			else:
				nextName = next.name

		# Something odd happens here; we've been getting:
		# AttributeError("'builtin_function_or_method' object has no attribute 'pop'")
		# But that implies we're getting a valid next object that is not a list.
		# FIXME: Debug this.
		except Exception as e:
			logging.error(f"{this.name} not proceeding to next: {e}; next: {nextName} (from {this.next})")
			return None

		if (next is None):
			logging.error(f"{this.name} not proceeding to next: {nextName} (None)")
			return None

		nextFunctor = next

		if (not this.warm):
			logging.warning(f"Please consider warming up {this.name} before using it in a sequence.")

		# Before preparations are made, let's clone what is to come.
		if (this.feature.sequence.clone):
			nextFunctor = deepcopy(next)
			kwargs = copy(this.kwargs)
			kwargs.update({'precursor':this, 'next':this.next})
			nextFunctor.WarmUp(*(next.args), **(kwargs))

		this.PrepareNext(nextFunctor)

		if (not this.ValidateNext(nextFunctor)):
			raise InvalidNext(f"Failed to validate {nextName}")

		if (this.abort.CallNext):
			logging.warning(f"{this.name} not proceeding to next: {nextName} (aborted)")
			this.abort.CallNext = False
			return None

		if (this.GetExecutor()):
			return this.GetExecutor().Execute(nextFunctor, precursor=this, next=this.next)

		return nextFunctor(precursor=this, next=this.next)


	# Prepare *this for any kind of operation.
	# All initialization should be done here.
	# RETURN boolean indicating whether or not *this is ready to do work.
	def WarmUp(this, *args, **kwargs):
		this.warm = False
		logging.debug(f"Warming up {this.name}...")

		if (this.feature.track):
			if (FunctorTracker.Instance().sequence.current.running):
				# We just started a new sequence. We're not ready to do work yet.
				if (FunctorTracker.Instance().sequence.stage[FunctorTracker.Instance().sequence.current.stage].state == 'initiated'):
					this.incomplete = True
					this.abort.WarmUp = True
					FunctorTracker.Instance().sequence.stage[FunctorTracker.Instance().sequence.current.stage].state = 'ready'
		# NOTE: this.abortWarmUp will (should) be set by the precursor before calling *this.

		if (not this.incomplete):
			this.args = []
			this.kwargs = {}

		this.args += args
		this.kwargs.update(kwargs)

		if (this.abort.WarmUp):
			this.abort.WarmUp = False
			return False

		this.result.code = 0
		this.result.data = util.DotDict()

		try:
			this.PopulatePrecursor()
			if (this.executor):
				this.executor.BeginPlacing(this.name)
			this.Initialize() # nop on call 2+
			this.PopulateMethods() # Doesn't require Fetch; depends on precursor
			this.ParseInitialArgs() # Usually where config is read in.
			this.ValidateStaticArgs() # nop on call 2+
			this.PopulateNext()
			this.ValidateArgs()
			this.ValidateMethods()
			if (this.executor):
				this.executor.ResolvePlacementOf(this.name)

		except Exception as e:

			# Allow partial function calls
			if (isinstance(e, MissingArgumentError) and this.feature.autoReturn):
				this.incomplete = True
				return False
			
			if (this.feature.raiseExceptions):
				raise e
			else:
				logging.error(f"ERROR: {e}")
				util.LogStack()

		this.incomplete = False
		this.warm = True
		return True


	# This is the () operator.
	# Child classes don't need to worry about this; all relevant logic is abstracted to Function.
	def __call__(this, *args, **kwargs) :
		if (this.feature.track):
			FunctorTracker.Push(this)
			this.Set('caller', FunctorTracker.GetLatest(1))

		args_repr = [repr(arg) for arg in args]
		kwargs_repr = {k: repr(v) for k, v in kwargs.items()}  
		logging.info(f"{this.name} ({args_repr}, {kwargs_repr}) {{")

		ret = None
		nextRet = None

		try:
			if (not this.warm or not set(args).issubset(set(this.args)) or not set(kwargs.keys()).issubset(set(this.kwargs.keys()))):
				this.WarmUp(*args, **kwargs)
			if (not this.feature.stayWarm):
				this.warm = False

			if (this.feature.track and this.feature.sequential):
				# TODO: Can we make this more performant? We should avoid doing this every time if we can.
				if (FunctorTracker.Instance().sequence.current.stage == 0 and this.WillPerformSequence()):
					FunctorTracker.InitiateSequence() # Has to be after WarmUp.

			if (this.incomplete):
				logging.debug(f"{this.name} incomplete.")
				logging.info(f"return {ret}")
				if (this.feature.track):
					FunctorTracker.Pop(this)
				logging.info(f"}} ({this.name})")
				return this

			logging.debug(f"{this.name}({this.args}, {this.kwargs})")

			getattr(this, f"Before{this.method.function}")()
			ret = getattr(this, this.method.function)()

			if (getattr(this, f"Did{this.method.function}Succeed")()):
					this.result.code = 0
					# logging.info(f"{this.name} successful!")
					nextRet = this.CallNext()
			elif (this.feature.rollback):
				logging.warning(f"{this.name} failed. Attempting Rollback...")
				ret = getattr(this, this.method.rollback)()
				if (getattr(this, f"Did{this.method.rollback}Succeed")()):
					this.result.code = 1
					# logging.info(f"Rollback succeeded. All is well.")
					nextRet = this.CallNext()
				else:
					this.result.code = 2
					logging.error(f"ROLLBACK FAILED! SYSTEM STATE UNKNOWN!!!")
			else:
				this.result.code = 3
				logging.error(f"{this.name} failed.")

			getattr(this, f"After{this.method.function}")()

		except Exception as e:
			if (this.feature.raiseExceptions):
				raise e
			else:
				logging.error(f"ERROR: {e}")
				util.LogStack()

		if (this.feature.raiseExceptions and this.result.code > 1):
			raise FunctorError(f"{this.name} failed with result {this.result.code}: {this.result}")

		if (nextRet is not None):
			ret = nextRet
		elif (this.feature.autoReturn):
			if (this.result.data is None):
				this.result.data = ret
			elif (not 'returned' in this.result.data):
					this.result.data.returned = ret
			else:
				pass

			ret = this

		logging.info(f"return {ret} ({[type(r) for r in ret] if type(ret) in [tuple, list] else type(ret)})")
		if (this.feature.track):
			FunctorTracker.Pop(this)
		logging.info(f"}} ({this.name})")

		return ret


	# Reduce the work required to access return values.
	# Make it possible to access related classes on the fly.
	def __getattr__(this, attribute):
		try:
			this.__getattribute__(attribute)
		except:
			try:
				return this.__dict__[attribute]
			except:
				try:
					return BackwardsCompatible.Get(this, attribute)
				except:
					try:
						# Easy access to return values.
						return this.result.data[attribute]
					except:
						try:
							fetchFrom = this.fetch.attr.use
							obj, found = this.Fetch(attribute, None, fetchFrom, start=False)
							if (found):
								return obj
							raise AttributeError(f"{this.name} has no attribute {attribute}")
						except:
							raise AttributeError(f"{this.name} has no attribute {attribute}")


	# Adapter for @recoverable.
	# See Recoverable.py for details
	def GetExecutor(this):
		return this.executor


	# Add support for deepcopy.
	# Copies everything besides methods; those will be created by PopulateMethods or removed.
	def __deepcopy__(this, memodict=None):
		logging.debug(f"Creating new {this.__class__} from {this.name}")
		cls = this.__class__
		ret = cls.__new__(cls)
		ret.__init__()

		memodict[id(this)] = ret

		# Huh?
		try:
			for key, val in [tup for tup in this.__dict__.items() if tup[0] not in ['methods']]:
				try:
					if (callable(val)):
						# PopulateMethods will take care of recreating skipped Methods
						# All other methods are dropped since they apparently have problems on some implementations.
						continue
					if (key in this.cloning.exclusions):
						continue
					setattr(ret, key, deepcopy(val, memodict))
				except:
					pass
		except:
			for key, val in [tup for tup in this.__dict__().items() if tup[0] not in ['methods']]:
				try:
					if (callable(val)):
						# PopulateMethods will take care of recreating skipped Methods
						# All other methods are dropped since they apparently have problems on some implementations.
						continue
					if (key in this.cloning.exclusions):
						continue
					setattr(ret, key, deepcopy(val, memodict))
				except:
					pass
		return ret


	# Enable sequences to be built/like/this
	def __truediv__(this, next):
		if (not this.feature.sequential):
			raise MissingMethodError(f"Please override __truediv__ for {this.name} ({type(this)}).")
		
		if (not isinstance(next, Functor)):
			return this
		
		this.next.append(next)
		next.abort.WarmUp = False
		return this.CallNext()


	# Avert your eyes!
	# This is deep black magick fuckery.
	# And no. There does not appear to be any other way to do this on CPython <=3.11
	def WillPerformSequence(this, backtrack=2):
		if (not this.feature.sequential):
			return False
		
		try:
			# NOTE: 11 is apparently the code for the __truediv__ division operator (/). On this system. For now...
			return [i for i in [i for i in dis.get_instructions(eval(f"inspect.currentframe(){'.f_back' * backtrack}.f_code")) if i.opname == 'BINARY_OP'] if i.arg == 11] > 0
		except:
			# Yeah...
			return False


	######## START: Fetch Locations ########

	def fetch_location_this(this, varName, default, fetchFrom, attempted):
		if (util.HasAttr(this, varName)):
			return util.GetAttr(this, varName), True
		return default, False

	def fetch_location_args(this, varName, default, fetchFrom, attempted):

		# this.args can't be searched.

		for key, val in this.kwargs.items():
			if (key == varName):
				return val, True
		return default, False


	def fetch_location_epidef(this, varName, default, fetchFrom, attempted):
		if (this.epidef is None):
			return default, False
		return this.epidef.FetchWithAndWithout(['this'], ['environment', 'globals', 'executor'], varName, default, fetchFrom, False, attempted)


	def fetch_location_caller(this, varName, default, fetchFrom, attempted):
		if (this.caller is None):
			return default, False
		return this.caller.FetchWithAndWithout(['this'], ['environment', 'globals', 'executor'], varName, default, fetchFrom, False, attempted)


	def fetch_location_precursor(this, varName, default, fetchFrom, attempted):
		if (this.precursor is None):
			return default, False
		return this.precursor.FetchWithAndWithout(['this'], ['environment', 'globals', 'executor'], varName, default, fetchFrom, False, attempted)



	# Call the Executor's Fetch method.
	# Exclude 'environment' because we can check that ourselves.
	def fetch_location_executor(this, varName, default, fetchFrom, attempted):
		if (not this.GetExecutor()):
			return default, False
		return this.GetExecutor().FetchWithout(['environment'], varName, default, fetchFrom, False, attempted)


	#NOTE: There is no config in the default Functor. This is done for the convenience of children.
	def fetch_location_config(this, varName, default, fetchFrom, attempted):
		if (not util.HasAttr(this, 'config') or this.config is None):
			return default, False

		for key, val in dict(this.config).items():
			if (key == varName):
				return val, True

		return default, False


	def fetch_location_globals(this, varName, default, fetchFrom, attempted):
		if (util.HasAttr(builtins, varName)):
			return util.GetAttr(builtins, varName), True
		return default, False


	def fetch_location_environment(this, varName, default, fetchFrom, attempted):
		envVar = os.getenv(varName)
		if (envVar is not None):
			return envVar, True
		envVar = os.getenv(varName.upper())
		if (envVar is not None):
			return envVar, True
		return default, False

	######## END: Fetch Locations ########
