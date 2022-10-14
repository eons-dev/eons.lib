import eons

class CustomSyntaxFunctor(eons.Functor):
	def __init__(this, name="HelloFunctor"):
		super().__init__(name)

		this.num = 0

		this.functionSucceeded = True
		this.rollbackSucceeded = True
		this.enableRollback = False

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		return this.TestFunction()


	@eons.method('CustomSyntaxMethod')
	def TestFunction(this):
		++this.num
		return this.num
