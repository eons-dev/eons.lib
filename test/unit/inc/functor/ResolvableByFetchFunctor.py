import logging
from inspect import getmodule
import eons

class ResolvableByFetchFunctor(eons.Functor):
	def __init__(this, name="ResolvableByFetchFunctor"):
		super().__init__(name)

		this.enableAutoReturn = False


	# Functor required method, see that class for details.
	def Function(this):
		return this.ResolvableFunction()


	# testdotdict is obviously not defined here.
	# What @eons.recoverable does is catch the resulting NameError and call /inc/resolve/resolve_find_by_fetch.by
	# That ErrorResolution will add testdotdict to this module's globals, making the following code valid.
	#
	# NOTE: READ ONLY ACCESS!
	# WE CANNOT MODIFY testdotdict
	@eons.recoverable
	def ResolvableFunction(this):
		return testdotdict.testval


	# Functor required method, see that class for details.
	def Rollback(this):
		pass


	# Functor required method, see that class for details.
	def DidFunctionSucceed(this):
		return True


	# Functor required method, see that class for details.
	def DidRollbackSucceed(this):
		return True

