from StandardTestFixture import StandardTestFixture
from Includes import Include, GetIncludePath

Include('inheritance')

class TestInheritance(StandardTestFixture):

	@classmethod # this is a lie
	def RegisterDirectories(this):
		super().RegisterDirectories()
		this.executor.RegisterAllClassesInDirectory(GetIncludePath('inheritance'))

	def test_inheritance_positive_control(this):
		assert(this.executor.GetRegistered('inheritance_positive_control') is not None)

	def test_inheriting_error_resolution(this):
		assert(this.executor.GetRegistered('inheriting_error_resolution') is not None)

	def test_inheriting_external(this):
		assert(this.executor.GetRegistered('inheriting_external') is not None)

