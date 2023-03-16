import logging
import eons
from StandardTestFixture import StandardTestFixture

class TestResolveByFetch(StandardTestFixture):

	def test_find_by_fetch(this):
		this.executor.extraArgs['testdotdict'] = {
			"testval": 5
		}

		assert(this.executor.Execute('ResolvableByFetchFunctor') == 5)

