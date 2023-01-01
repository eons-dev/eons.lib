import pytest
import logging
import gc
import eons
from StandardTestFixture import StandardTestFixture

class TestGlobalFetch(StandardTestFixture):

	def test_global_fetch(this):

		# The StandardTestFixture should create a DummyExecutor named "Standard Test Executor".
		# Let's test that.
		expectedName = this.executor.name
		assert(eons.Fetch("name") == expectedName)

		# Depending on how this test is run, there may be other executors registered besides the DummyExecutor (e.g. EBBS).
		execs = len(eons.ExecutorTracker.Instance().executors)

		# Deleting the Executor should remove it from the tracker.
		# del this.executor raises: AttributeError: 'TestGlobalFetch' object has no attribute 'executor'
		# And, beyond that, the reference count to the executor is WAY higher than it should be.
		# So, we'll just manually pop it from the tracker.
		eons.ExecutorTracker.Instance().Pop(this.executor)
		assert(len(eons.ExecutorTracker.Instance().executors) == (execs - 1))

		# Now, let's make sure we broke it.
		assert(eons.Fetch("name") != expectedName)
