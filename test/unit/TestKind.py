from StandardTestFixture import StandardTestFixture

class TestKindFixture(StandardTestFixture):

	def test_kind(this):
		kindResult = this.executor.Execute('KindFunctor')
		assert (kindResult == {
			'kind result': "HelloFunctor (external) says hello to simplicity!"
		})
