import logging
import ctypes

# ExecutorTracker is a global singleton which keeps a record of all Executors that have been launched.
# This can be abused quite a bit, so please try to restrict usage of this to only:
# * Ease of use global functions
#
# Thanks! 
class ExecutorTracker:
	def __init__(this):
		# Singletons man...
		if "instance" not in ExecutorTracker.__dict__:
			logging.debug(f"Creating new ExecutorTracker: {this}")
			ExecutorTracker.instance = this
		else:
			return None

		this.executors = [None]

	@staticmethod
	def Instance():
		if "instance" not in ExecutorTracker.__dict__:
			ExecutorTracker()
		return ExecutorTracker.instance

	@staticmethod
	def Push(executor):
		ExecutorTracker.Instance().executors.append(executor)

		# Adding the executor to our list here increases its reference count.
		# Executors are supposed to remove themselves from this list when they are deleted.
		# A python object cannot be deleted if it has references.
		# Thus, we forcibly decrease the reference count and rely on Exectuor's self-reporting to avoid accessing deallocated memory.
		ctypes.pythonapi.Py_DecRef(ctypes.py_object(executor))

		logging.debug(f"Now tracking Executor: {executor}")

	@staticmethod
	def Pop(executor):
		try:
			ExecutorTracker.Instance().executors.remove(executor)
			logging.debug(f"No longer tracking Executor: {executor}")
		except:
			pass

	@staticmethod
	def GetLatest():
		return ExecutorTracker.Instance().executors[-1]
