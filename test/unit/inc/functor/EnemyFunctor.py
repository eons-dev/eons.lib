import eons

class EnemyFunctor(eons.Functor):
	def __init__(this, name="EnemyFunctor"):
		super().__init__(name)

		this.requiredMethods.append('Hello')

		this.requiredKWArgs.append('enemy')

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		return this.Hello(f"its {this.enemy} Enemy")


	# Undo any changes made by UserFunction.
	# Please override this too!
	def Rollback(this):
		pass


	# Override this to check results of operation and report on status.
	# Override this to perform whatever success checks are necessary.
	def DidFunctionSucceed(this):
		return True


	# RETURN whether or not the Rollback was successful.
	# Override this to perform whatever success checks are necessary.
	def DidRollbackSucceed(this):
		return True

