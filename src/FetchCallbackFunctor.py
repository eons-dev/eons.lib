from .Functor import Functor

class FetchCallbackFunctor(Functor):

	def __init__(this, name = "FetchCallbackFunctor"):
		super().__init__(name)

		this.arg.kw.required.append('varName')
		this.arg.kw.required.append('location')
		this.arg.kw.required.append('value')

		this.functionSucceeded = True
		this.feature.rollback = False