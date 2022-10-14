import logging
import traceback
#from .Executor import Executor # don't import this, it'll be circular!
from .Exceptions import *

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

		logging.warning(f"Got error '{e}' from function ({function}) by {obj.name}.")
		if (executor.parsedArgs.verbose > 0 and executor.parsedArgs.quiet == 0):
			traceback.print_exc()

		# We have to use str(e) instead of pointers to Exception objects because multiple Exceptions will have unique addresses but will still be for the same error, as defined by string comparison.
		if (str(e) not in executor.errorResolutionStack.keys()):
			executor.errorResolutionStack.update({str(e):[]})

		# ResolveError should be the only method which adds to executor.errorResolutionStack.
		# ResolveError is itself @recoverable.
		# So, each time we hit this point, we should also hit a corresponding ClearErrorResolutionStack() call. 
		# If we do not, an exception is passed to the caller; if we do, the stack will be cleared upon the last resolution.
		executor.errorRecursionDepth = executor.errorRecursionDepth + 1

		if (executor.errorRecursionDepth > len(executor.errorResolutionStack.keys())+1):
			raise FailedErrorResolution(f"Hit infinite loop trying to resolve errors. Recursion depth: {executor.errorRecursionDepth}; STACK: {executor.errorResolutionStack}.")

		for i, res in enumerate(executor.resolveErrorsWith):

			logging.debug(f"Checking if {res} can fix '{e}'.")
			if (not executor.ResolveError(e, i)): # attempt to resolve the issue; might cause us to come back here with a new error.
				# if no resolution was attempted, there's no need to re-run the function.
				continue
			try:
				logging.debug(f"Trying function ({function}) again after applying {res}.")
				ret = function(obj, *args, **kwargs)
				executor.ClearErrorResolutionStack(str(e)) # success!
				logging.info(f"{res} successfully resolved '{e}'!")
				logging.debug(f"Error stack is now: {executor.errorResolutionStack}")
				return ret
			except Exception as e2:
				logging.debug(f"{res} failed with '{e2}'; will ignore and see if we can use another ErrorResolution to resolve '{e}'.")
				# Resolution failed. That's okay. Let's try the next.
				# Not all ErrorResolutions will apply to all errors, so we may have to try a few before we get one that works.
				pass

		#  We failed to resolve the error. Die
		raise FailedErrorResolution(f"Tried and failed to resolve: {e} STACK: {executor.errorResolutionStack}.")
