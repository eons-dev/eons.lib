import eons

class CustomSyntaxFunctor(eons.Functor):
	def __init__(this, name="CustomSyntaxFunctor"):
		super().__init__(name)

		this.num = 0

		this.functionSucceeded = True
		this.rollbackSucceeded = True
		this.feature.rollback = False
		this.feature.autoReturn = False

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		return this.TestFunction()


	@eons.method('CustomSyntaxMethod')
	def TestFunction(this):
		++this.num
		return this.num
