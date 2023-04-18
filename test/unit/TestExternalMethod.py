from StandardTestFixture import StandardTestFixture

class TestExternalMethodFixture(StandardTestFixture):

	def test_external_hello(this):
		simpleHello = this.executor.Execute('ExternalHelloFunctor')
		assert (simpleHello == "HelloFunctor (external) says hello to all the exeternal possibilities!")
