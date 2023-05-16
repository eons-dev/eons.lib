import logging

# FunctorTracker is a global singleton which keeps a record of all functors that are currently in the call stack.
# Functors should add and remove themselves from this list when they are called.
class FunctorTracker:
	def __init__(this):
		# Singletons man...
		if "instance" not in FunctorTracker.__dict__:
			logging.debug(f"Creating new FunctorTracker: {this}")
			FunctorTracker.instance = this
		else:
			return None

		this.functors = [None]

	@staticmethod
	def Instance():
		if "instance" not in FunctorTracker.__dict__:
			FunctorTracker()
		return FunctorTracker.instance

	@staticmethod
	def Push(functor):
		FunctorTracker.Instance().functors.append(functor)

	# Remove the last instance of the functor from the list.
	@staticmethod
	def Pop(functor):
		tracker = FunctorTracker.Instance()
		tracker.functors.reverse()
		try:
			tracker.functors.remove(functor)
		except:
			pass
		tracker.functors.reverse()

	@staticmethod
	def GetCount():
		return len(FunctorTracker.Instance().functors)
