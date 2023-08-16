import logging
import eons

# External Methods replace a function with a Functor retrieved from outside the caller's module.
# The function's name should match the name of the Functor that will replace it.
# The function need not take any arguments beyond *this.
class External(eons.Method):
	def __init__(this, name="External Method"):
		super().__init__(name)

		this.feature.rollback = False
		this.functionSucceeded = True
		this.rollbackSucceeded = True

		this.type = None
		this.functorName = ""
		this.functor = None

	def UpdateSource(this):
		if (not this.type):
			this.type = eons.ExecutorTracker.GetLatest().default.package.type
		try:
			this.functor = eons.ExecutorTracker.GetLatest().GetRegistered(this.functorName, this.type, namespace = this.caller.name)
		except:
			this.functor = eons.ExecutorTracker.GetLatest().GetRegistered(this.functorName, this.type)

		if (not this.functor):
			raise eons.MissingMethodError(f"Could not populate external method {this.functorName} (type {this.type})")
		
		this.functor.name = f"{this.functor.name} (external)"
		this.feature = this.functor.feature

		# To allow this.functor to be called with *args, we must also allow this to be called with *args (+ this).
		this.arg.mapping += this.functor.arg.mapping

	def PopulateFrom(this, function):
		this.functorName = function.__name__

	def GetKWArgsForMethod(this):
		kwargs = this.kwargs
		kwargs.update({
			'executor': this.executor,
			'precursor': this,
		})
		this.functor.caller = this.caller
		return kwargs
	
	def WarmUp(this, *args, **kwargs):
		super().WarmUp(*args, **kwargs)
		this.functor.WarmUp(*this.args[1:], **this.GetKWArgsForMethod())

	def Function(this):
		ret = this.functor.Function()
		this.result = this.functor.result
		return ret

	def Rollback(this):
		ret = this.functor.Rollback()
		this.result = this.functor.result
		return ret
	
	def DidFunctionSucceed(this):
		return this.functor.DidFunctionSucceed()
	
	def DidRollbackSucceed(this):
		return this.functor.DidRollbackSucceed()