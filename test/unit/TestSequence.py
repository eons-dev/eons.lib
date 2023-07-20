from StandardTestFixture import StandardTestFixture
import eons

class TestSequenceFixture(StandardTestFixture):

	def test_sequence(this):
		# These 2 means of getting a SelfRegistering object should be equal.
		sequenceParent = eons.SelfRegistering('SequenceParentFunctor')
		partialFunctor = this.executor.GetRegistered('PartialFunctor')

		sequenceParent.executor = this.executor
		partialFunctor.executor = this.executor

		sequenceResult = sequenceParent(['HAPPY', 'HAPPY', 'BOOM', 'BOOM', 'SWAMP', 'SWAMP', 'SWAMP!']) / partialFunctor(separator = ', ')
		sequenceResult = sequenceResult.returned
		assert (sequenceResult == "HelloFunctor (external) says hello to HAPPY, HAPPY, BOOM, BOOM, SWAMP, SWAMP, SWAMP!")