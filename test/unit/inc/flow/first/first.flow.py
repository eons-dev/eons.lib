import eons

class first(eons.Functor):
	def __init__(this, name="first"):
		super().__init__(name)

		this.functionSucceeded = True
		this.feature.rollback = False
		this.feature.autoReturn = False
		
	@eons.method(impl="External")
	def second(this):
		pass

	def Function(this):
		return {"value": 1}