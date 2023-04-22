import logging
import eons

# External Methods replace a function with a Functor retrieved from outside the caller's module.
# The function's name should match the name of the Functor that will replace it.
# The function need not take any arguments beyond *this.
class External(eons.Method):
	def __init__(this, name="External Method"):
		super().__init__(name)

		this.enableRollback = False
		this.functionSucceeded = True
		this.rollbackSucceeded = True

		this.type = None
		this.functorName = ""
		this.functor = None

	def UpdateSource(this):
		if (not this.type):
			this.type = eons.ExecutorTracker.GetLatest().defaultPackageType

		this.functor = eons.ExecutorTracker.GetLatest().GetRegistered(this.functorName, this.type)

		if (not this.functor):
			raise eons.MissingMethodError(f"Could not populate external method {this.functorName} (type {this.type})")
		
		this.functor.name = f"{this.functor.name} (external)"

		# To allow this.functor to be called with *args, we must also allow this to be called with *args.
		this.argMapping = this.functor.argMapping

	def PopulateFrom(this, function):
		this.functorName = function.__name__

	def Function(this):
		kwargs = this.kwargs
		kwargs.update({
			'executor': this.executor,
			'precursor': this
		})
		return this.functor(*this.args, **kwargs)
	