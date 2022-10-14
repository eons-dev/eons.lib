import eons
import sys
import logging

#Try resolving a ModuleNotFoundError by installing the module through our repo.
class install_from_repo(eons.ErrorResolution):
	def __init__(this, name="install_with_pip"):
		super().__init__(name)

		this.ApplyTo('HelpWantedWithRegistering', "Trying to get SelfRegistering OBJECT")
		this.ApplyTo('ModuleNotFoundError', "No module named 'OBJECT'")

	def Resolve(this):
		this.errorShouldBeResolved = this.executor.DownloadPackage(this.errorObject)
