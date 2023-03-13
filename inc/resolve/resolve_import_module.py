import eons
import logging
import inspect
import importlib
import sys

# Try to import the package.
class import_module(eons.ErrorResolution):
	def __init__(this, name="import_module"):
		super().__init__(name)

		this.ApplyTo('NameError', "name 'OBJECT' is not defined")

	def Resolve(this):
		if (this.errorObject not in sys.modules.keys()):
			this.errorShouldBeResolved = False
			return

		moduleToHack = inspect.getmodule(this.function)
		setattr(moduleToHack, this.errorObject, sys.modules[this.errorObject])
		this.errorShouldBeResolved = True
