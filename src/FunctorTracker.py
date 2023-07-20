import logging
from .Utils import util

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

		this.sequence = util.DotDict()
		this.sequence.current = util.DotDict()
		this.sequence.current.running = False
		this.sequence.current.stage = 0
		this.sequence.stage = []

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

	@staticmethod
	def InitiateSequence():
		FunctorTracker.Instance().sequence.current.running = True
		FunctorTracker.Instance().sequence.current.stage += 1
		FunctorTracker.Instance().sequence.stage.append(util.DotDict({'state': 'initiated'}))

	@staticmethod
	def CompleteSequence():
		if (not FunctorTracker.Instance().sequence.current.running):
			return
		FunctorTracker.Instance().sequence.current.stage -= 1
		FunctorTracker.Instance().sequence.stage.pop()
		FunctorTracker.Instance().sequence.current.running = FunctorTracker.Instance().sequence.current.stage > 0
