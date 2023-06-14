import logging
from StandardTestFixture import StandardTestFixture

class TestSyntaxControl(StandardTestFixture):

	def test_custom_syntax(this):
		tests = [
			0,
			1,
			2
		]
		for i, expected in enumerate(tests):
			result = this.executor.Execute('CustomSyntaxFunctor')
			logging.debug(f"Test {i}: Got {result} while expecting {expected}")
			assert(result == expected)

