import os
import logging
import eons as e

class TESTEXECUTOR(e.Executor):

	def __init__(this):

		super().__init__(name="test executor", description="TESTING ONLY")

	#Override of eons.Executor method. See that class for details
	def Configure(this):
		super().Configure()

		# this.logLevel = logging.getLogger().level

	#Override of eons.Executor method. See that class for details
	def Function(this):
		logging.getLogger().setLevel(logging.CRITICAL)

		super().Function()

		hello = this.GetRegistered("hello_world", "functor")
		hello.ableAutoReturn = False
		hello(executor=this)

	def PostCall(this):
		# logging.getLogger().setLevel(this.logLevel)
		pass

