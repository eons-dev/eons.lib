import eons

class HelloFunctor(eons.StandardFunctor):
	def __init__(this, name="HelloFunctor"):
		super().__init__(name)

		this.optionalKWArgs['say_hi_to'] = 'you'

		this.argMapping.append('say_hi_to')

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		return this.Hello(f"{this.say_hi_to}")


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


	# RETURNS: an opened file object for writing.
	# Creates the path if it does not exist.
	@eons.method(propagate=True)
	def Hello(this, to_whom):
		return f'{this.name} says hello to {to_whom}'
