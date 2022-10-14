import logging
import eons
from Includes import Include, GetIncludePath

Include('executor')

from DummyExecutor import DummyExecutor

class StandardTestFixture(object):

	# Pytest skips classes with __init__ methods.
	# That's dumb.
	# It seems like the best we can do atm is add our members as class members which should be re-instantiated before every test.
	@classmethod
	def setup_class(cls):
		cls.Constructor()

	@classmethod # this is a lie.
	def Constructor(this):
		logging.debug(f"Constructing {this.__name__}")
		this.executor = DummyExecutor("Standard Test Executor")
		this.SetExecutorArgs()
		this.executor()
		this.RegisterDirectories()

	@classmethod # this is a lie.
	def SetExecutorArgs(this):
		# Spoof CLI args.
		this.executor.parsedArgs = eons.util.DotDict({
			'no_repo': True,
			'verbose': 1,
			'quiet': 0,
			'config': None
		})
		this.executor.extraArgs = {}

	@classmethod # this is a lie.
	def RegisterDirectories(this):

		# Order matters
		# Skip executor
		register = [
			'method', #Should be first
			'datum',
			'data_container',
			'functor'
		]
		for r in register:
			this.executor.RegisterAllClassesInDirectory(GetIncludePath(r))

