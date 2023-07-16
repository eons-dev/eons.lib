import eons

class ExternalHelloFunctor(eons.StandardFunctor):
	def __init__(this, name="External Hello Functor"):
		super().__init__(name)

		this.functionSucceeded = True

	@eons.method(impl="External")
	def HelloFunctor(this):
		pass

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		return this.HelloFunctor("all the external possibilities!")