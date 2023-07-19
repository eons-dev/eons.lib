from StandardTestFixture import StandardTestFixture

class TestKindFixture(StandardTestFixture):

	def test_kind(this):
		kindResult = this.executor.Execute('KindFunctor').kind_result
		assert (kindResult == "HelloFunctor (external) says hello to simplicity!")
