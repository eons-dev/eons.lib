import pytest
import logging
import gc
import eons
from StandardTestFixture import StandardTestFixture

class TestGlobalFetch(StandardTestFixture):

	def test_global_fetch(this):

		# The StandardTestFixture should create a DummyExecutor named "Standard Test Executor".
		expectedName = "Test Global Fetch Executor"
		this.executor.name = expectedName
		assert(eons.Fetch("name") == expectedName)

		# Depending on how this test is run, there may be other executors registered besides the DummyExecutor (e.g. EBBS).
		expectedExecutorCount = len(eons.ExecutorTracker.Instance().executors) -1

		# Deleting the Executor should remove it from the tracker.
		# del this.executor raises: AttributeError: 'TestGlobalFetch' object has no attribute 'executor'
		# And, beyond that, the reference count to the executor is WAY higher than it should be.
		# So, we'll just manually pop it from the tracker.
		eons.ExecutorTracker.Instance().Pop(this.executor)
		assert(len(eons.ExecutorTracker.Instance().executors) == expectedExecutorCount)

		# Now, let's make sure we broke it.
		if (expectedExecutorCount == 1): # None can't be Fetched from.
			with pytest.raises(Exception):
				assert(eons.Fetch("name") != expectedName)
		else: # if there is more than 1 executor registered.
			assert(eons.Fetch("name") != expectedName)
