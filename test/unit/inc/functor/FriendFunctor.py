import eons
from HelloFunctor import HelloFunctor

class FriendFunctor(HelloFunctor):
	def __init__(this, name="FriendFunctor"):
		super().__init__(name)

		this.enableAutoReturn = False

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		return this.Hello(f"its {this.say_hi_to} Friend")
