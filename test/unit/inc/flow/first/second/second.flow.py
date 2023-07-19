import eons

class second(eons.Functor):
	def __init__(this, name="second"):
		super().__init__(name)

		this.functionSucceeded = True
		this.enableRollback = False
		this.enableAutoReturn = False

	def Function(this):
		return {"value": 2}