import logging
#from .Executor import Executor # don't import this, it'll be circular!
from .Exceptions import *
from .Utils import util

# @recoverable
# Decorating another function with this method will engage the error recovery system provided by *this.
# To use this, you must define a GetExecutor() method in your class and decorate the functions you want to recover from.
# For more info, see Executor.ResolveError and the README.md
def recoverable(function):
	def RecoverableDecorator(obj, *args, **kwargs):
		return RecoverableImplementation(obj, obj.GetExecutor(), function, *args, **kwargs)
	return RecoverableDecorator


# This needs to be recursive, so rather than having the recoverable decorator call or decorate itself, we just break the logic into this separate method.
def RecoverableImplementation(obj, executor, function, *args, **kwargs):
	try:
		return function(obj, *args, **kwargs)
	except FailedErrorResolution as fatal:
		raise fatal
	except Exception as e:
		if (not executor.resolveErrors):
			raise e
		return Recover(e, obj, executor, function, *args, **kwargs)


def Recover(error, obj, executor, function, *args, **kwargs):
	logging.warning(f"Got error '{error}' from function ({function}) by {obj.name}.")
	util.LogStack()

	# We have to use str(e) instead of pointers to Exception objects because multiple Exceptions will have unique addresses but will still be for the same error, as defined by string comparison.
	if (str(error) not in executor.errorResolutionStack.keys()):
		executor.errorResolutionStack.update({str(error):[]})

	# The executor.errorResolutionStack grows each time we invoke *this or (indirectly) executor.ResolveError().
	# ResolveError is itself @recoverable.
	# So, each time we hit this point, we should also hit a corresponding ClearErrorResolutionStack() call.
	# If we do not, an exception is passed to the caller; if we do, the stack will be cleared upon the last resolution.
	executor.errorRecursionDepth = executor.errorRecursionDepth + 1

	if (executor.errorRecursionDepth > len(executor.errorResolutionStack.keys())+1):
		raise FailedErrorResolution(f"Hit infinite loop trying to resolve errors. Recursion depth: {executor.errorRecursionDepth}; STACK: {executor.errorResolutionStack}.")

	successfullyRecovered = False
	ret = None
	resolvedBy = None
	for i, res in enumerate(executor.resolveErrorsWith):

		logging.debug(f"Checking if {res} can fix '{error}'.")
		if (not executor.ResolveError(error, i, obj, function)): # attempt to resolve the issue; might cause us to come back here with a new error.
			# if no resolution was attempted, there's no need to re-run the function.
			continue
		try:
			logging.debug(f"Trying function ({function}) again after applying {res}.")
			resolvedBy = res
			ret = function(obj, *args, **kwargs)
			successfullyRecovered = True
			break

		except Exception as e2:
			if (str(error) == str(e2)):
				logging.debug(f"{res} failed with '{e2}'; will ignore and see if we can use another ErrorResolution to resolve '{error}'.")
				# Resolution failed. That's okay. Let's try the next.
				# Not all ErrorResolutions will apply to all errors, so we may have to try a few before we get one that works.
				continue
			else:
				# The error changed, maybe we're making progress.
				ret = Recover(e2, obj, executor, function, *args, **kwargs)
				successfullyRecovered = True
				break

	if (successfullyRecovered):
		executor.ClearErrorResolutionStack(str(error)) # success!
		logging.recovery(f"{resolvedBy} successfully resolved '{error}'!")
		logging.debug(f"Error stack is now: {executor.errorResolutionStack}")
		return ret

	#  We failed to resolve the error. Die
	sys.tracebacklimit = 0 # traceback is NOT helpful here.
	raise FailedErrorResolution(f"Tried and failed to resolve: {error} STACK: {executor.errorResolutionStack}. See earlier logs (in debug) for traceback.")
