import eons

class second(eons.Functor):
	def __init__(this, name="second"):
		super().__init__(name)

		this.functionSucceeded = True
		this.feature.rollback = False
		this.feature.autoReturn = False

	def Function(this):
		return {"value": 2}