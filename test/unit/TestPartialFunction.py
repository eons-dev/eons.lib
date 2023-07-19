from StandardTestFixture import StandardTestFixture
import eons

class TestPartialFunctionFixture(StandardTestFixture):

	def test_partial_function(this):
		partialFunctor = eons.SelfRegistering("PartialFunctor")
		partialFunctor.executor = this.executor
		result = partialFunctor(words=["AAAAAA", "HELP!"])(separator="! ").returned
		assert (result == "HelloFunctor (external) says hello to AAAAAA! HELP!")
