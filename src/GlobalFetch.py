from .ExecutorTracker import ExecutorTracker

# Global Fetch() function.
# Uses the latest registered Executor
def Fetch(varName, default=None, fetchFrom=None, start=True, attempted=None):
    return ExecutorTracker.GetLatest().Fetch(varName, default, fetchFrom, start, attempted)

# Ease-of-use wrapper for the global Fetch()
def f(varName, default=None, fetchFrom=None, start=True, attempted=None):
    Fetch(varName, default, fetchFrom, start, attempted)