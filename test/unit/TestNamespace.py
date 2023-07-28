from StandardTestFixture import StandardTestFixture
import eons

class TestConflict3:
	def __init__(this, executor):
		this.name = 'TestConflict3'
		this.executor = executor

	def GetExecutor(this):
		return this.executor
	
	# For some reason, recoverable methods do not work within pytest fixtures.
	@eons.recoverable
	def get_c3_conflict_num(this, c3):
		ret = c3/conflict
		return ret.returned

class TestNamespaceFixture(StandardTestFixture):
	
	# Make sure GetRegistered properly accounts for namespaces.
	def test_namespace_coexistence(this):
		c1 = this.executor.GetRegistered('conflict', namespace = 'conflict1')
		c2 = this.executor.GetRegistered('conflict', namespace = 'conflict2')
		assert(
			c1(executor = this.executor).returned
			!= c2(executor = this.executor).returned
		)

	# Simulate a function call without ever defining the Functor class
	# This should trigger the error resolution machinery on an AttributeError, which should cause resolve_namespace_lookup to search through the FunctorTracker list for a namespace which matches the Functor's name.
	def test_sequential_namespace_resolution(this):
		c3 = eons.Functor('conflict3')
		t3 = TestConflict3(this.executor)
		eons.FunctorTracker.Push(c3)
		n3 = t3.get_c3_conflict_num(c3)
		eons.FunctorTracker.Pop(c3)
		assert(n3 == 3)

	# Above we test the `/` notation on previously unlinked Functors.
	# Here we test the `.`notation to ensure namespaced dependency injection is working.
	def test_namespace_injection(this):
		c4 = this.executor.GetRegistered('conflict4')
		c4.WarmUp(executor = this.executor)
		assert(c4.conflict().returned == 4)