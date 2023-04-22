from StandardTestFixture import StandardTestFixture
from Includes import Include, GetIncludePath
import eons
import logging

class TestFlow(StandardTestFixture):

	def test_flow(this):
		assert(this.executor.Flow('second.first') == {"value": 2})