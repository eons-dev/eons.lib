import eons
import sys
import logging

# Try resolving a ModuleNotFoundError by installing the module through our repo.
# This is useful for resolving implicit imports from the repo.
class install_from_repo_with_default_package_type(eons.ErrorResolution):
	def __init__(this, name="install_with_pip"):
		super().__init__(name)

		this.ApplyTo('ModuleNotFoundError', "No module named 'OBJECT'")
		this.ApplyTo('NameError', "name 'OBJECT' is not defined")

	def Resolve(this):
		this.errorShouldBeResolved = this.executor.DownloadPackage(f"{this.errorObject}.{this.executor.defaultPackageType}")
