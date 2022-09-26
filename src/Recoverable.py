#from .Executor import Executor # don't import this, it'll be circular!
from .Exceptions import *

# @recoverable
# Decorating another function with this method will engage the error recovery system provided by *this.
# To use this, you must define a GetExecutor() method in your class and decorate the functions you want to recover from.
# For more info, see Executor.ResolveError and the README.md
def recoverable(function):
    def method(obj, *args, **kwargs):
        return RecoverableImplementation(obj, obj.GetExecutor(), function, None, *args, **kwargs)
    return method


# This needs to be recursive, so rather than having the recoverable decorator call or decorate itself, we just break the logic into this separate method.
def RecoverableImplementation(obj, executor, function, lastError, *args, **kwargs):
    try:
        return function(obj, *args, **kwargs)
    except FailedErrorResolution as fatal:
        raise fatal
    except Exception as e:
        if (not executor.resolveErrors):
            raise e

        # If we already tried handling this error for this function call, something is wrong. abort.
        if (lastError and lastError == e):
            raise FailedErrorResolution(f"Error could not be resolved: {lastError}")

        # ResolveError should be the only method which adds to executor.errorResolutionStack.
        # ResolveError is itself @recoverable.
        # So, each time we hit this point, we should also hit a corresponding ClearErrorResolutionStack() call. 
        # If we do not, an exception is passed to the caller; if we do, the stack will be cleared upon the last resolution.
        executor.errorRecursionDepth = executor.errorRecursionDepth + 1

        for i, res in enumerate(executor.resolveErrorsWith):

            if (not executor.ResolveError(e, i)): # attempt to resolve the issue; might cause us to come back here with a new error.
                # if no resolution was attempted, there's no need to re-run the function.
                continue
            try:
                ret = function(obj, *args, **kwargs)
                executor.ClearErrorResolutionStack() # success!
                return ret
            except:
                # Resolution failed. That's okay. Let's try the next.
                # Not all ErrorResolutions will apply to all errors, so we may have to try a few before we get one that works.
                pass

        #  We failed to resolve the error. Die
        raise FailedErrorResolution(f"Tried and failed to resolve: {e}")