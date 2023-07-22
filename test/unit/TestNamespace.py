from StandardTestFixture import StandardTestFixture

class TestNamespaceFixture(StandardTestFixture):
	
	def test_namespace_coexistence(this):
		c1 = this.executor.GetRegistered('conflict', namespace = 'conflict1')
		c2 = this.executor.GetRegistered('conflict', namespace = 'conflict2')
		assert(
			c1(executor = this.executor).returned
			!= c2(executor = this.executor).returned
		)