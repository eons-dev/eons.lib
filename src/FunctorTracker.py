import logging
from .Utils import util
from .Namespace import Namespace

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
		if (functor is None or not functor.feature.track):
			logging.debug(f"Refusing to track {functor}")
			return

		FunctorTracker.Instance().functors.append(functor)

	# Remove the last instance of the functor from the list.
	@staticmethod
	def Pop(functor):
		if (functor is None or not functor.feature.track):
			logging.debug(f"Refusing to untrack {functor}")
			return

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
	def GetLatest(backtrack=0):
		try:
			return FunctorTracker.Instance().functors[-1 - backtrack]
		except:
			return None

	# Add a sequence to *this.
	@staticmethod
	def InitiateSequence():
		FunctorTracker.Instance().sequence.current.running = True
		FunctorTracker.Instance().sequence.current.stage += 1
		FunctorTracker.Instance().sequence.stage.append(util.DotDict({'state': 'initiated'}))

	# Remove a sequence from *this.
	@staticmethod
	def CompleteSequence():
		if (not FunctorTracker.Instance().sequence.current.running):
			return
		FunctorTracker.Instance().sequence.current.stage -= 1
		FunctorTracker.Instance().sequence.stage.pop()
		FunctorTracker.Instance().sequence.current.running = FunctorTracker.Instance().sequence.current.stage > 0

	
	# Calculate the current namespace, trimming off the last backtrack number of namespaces.
	# The first Functor we Track is likely the Executor, so make sure to skip that.
	@staticmethod
	def GetCurrentNamespace(backtrack=0, start=1):
		return Namespace([functor.name for functor in FunctorTracker.Instance().functors[start:len(FunctorTracker.Instance().functors) - (backtrack+1)]])

	# Get the current namespace as a python usable Functor name.
	@staticmethod
	def GetCurrentNamespaceAsName(backtrack=0, start=1):
		return Namespace.ToName(FunctorTracker.GetCurrentNamespace(start, backtrack))
