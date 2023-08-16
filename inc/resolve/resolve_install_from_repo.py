import eons
import sys
import logging

# Try resolving a ModuleNotFoundError by installing the module through our repo.
class install_from_repo(eons.ErrorResolution):
	def __init__(this, name="install_from_repo"):
		super().__init__(name)

		this.ApplyTo('HelpWantedWithRegistering', "Trying to get SelfRegistering SUBJECT")
		this.ApplyTo('ModuleNotFoundError', "No module named 'SUBJECT'")

	def Resolve(this):
		this.error.resolution.successful = this.executor.DownloadPackage(this.error.subject)
