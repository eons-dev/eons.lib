import pytest
import logging
import shutil
from pathlib import Path
from StandardTestFixture import StandardTestFixture

class TestPackageDownload(StandardTestFixture):

	# Try to get a non-existent SelfRegistering without downloading a package from the infrastructure repository.
	# Should fail.
	def test_package_download_without_repo(this):
		#Make sure test package doesn't exist.
		#package_test is avaliable from infrastructure.tech.
		with pytest.raises(Exception):
			this.executor.GetRegistered("eonstestpackage")
			assert(False) # just in case something was missed.

		with pytest.raises(Exception):
			this.executor.GetRegistered("eonstestpackage", "package")
			assert(False) # just in case something was missed.


	# Try downloading a package from the infrastructure repository.
	# Should try to download https://infrastructure.tech/package/package_test and succeed.
	def test_package_download_with_repo(this):

		this.executor.repo.online = True

		# For some reason, the name 'test' is unusable if this line is included.
		# AND InheritingClasses calls 'import apie'.
		# This line comes from TestInheritance and will be run before *this under normal circumstances (i.e. when running all tests).
		# 'test' has thus been renamed to 'eonstestpackage'
		# executor.RegisterAllClassesInDirectory(registerPath)

		# Don't want stale data from the previous test
		# FIXME: How are we getting stale data from the previous test?!?!
		this.executor.ClearErrorResolutionStack(force=True)

		# Use a fake repo.store so that we don't destroy a shared resource.
		origRepoStore = this.executor.repo.store
		tmpRepoStore = "/tmp/__test_repo_store"
		this.executor.repo.store = tmpRepoStore
	
		if (Path(this.executor.repo.store).exists()):
			logging.info(f"Deleting: {this.executor.repo.store}")
			shutil.rmtree(this.executor.repo.store)

		test = this.executor.GetRegistered("eonstestpackage", "package")
		assert(test is not None)
		test(executor=this.executor)
		assert(test.result.code == 0)

		this.executor.repo.store = origRepoStore
