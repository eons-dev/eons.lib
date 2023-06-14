from .Functor import Functor

class FetchCallbackFunctor(Functor):

	def __init__(this, name = "FetchCallbackFunctor"):
		super().__init__(name)

		this.requiredKWArgs.append('varName')
		this.requiredKWArgs.append('location')
		this.requiredKWArgs.append('value')

		this.functionSucceeded = True
		this.enableRollback = False