import eons
import sys
import logging

# Try resolving a ModuleNotFoundError by installing the module with pip.
class install_with_pip(eons.ErrorResolution):
	def __init__(this, name="install_with_pip"):
		super().__init__(name)

		this.ApplyTo('ModuleNotFoundError', "No module named 'OBJECT'")

	def Resolve(this):
		this.RunCommand(f"{sys.executable} -m pip install {this.errorObject}")
