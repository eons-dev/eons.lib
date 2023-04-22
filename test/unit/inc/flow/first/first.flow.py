import eons

class first(eons.Functor):
	def __init__(this, name="first"):
		super().__init__(name)

		this.functionSucceeded = True
		this.enableRollback = False
		
	@eons.method(impl="External")
	def second(this):
		pass

	def Function(this):
		return {"value": 1}