import eons
import logging
import inspect
import importlib
import sys

# Try to import the package.
class import_module(eons.ErrorResolution):
	def __init__(this, name="import_module"):
		super().__init__(name)

		this.ApplyTo('NameError', "name 'SUBJECT' is not defined")

	def Resolve(this):
		if (this.error.subject not in sys.modules.keys()):
			this.error.resolution.successful = False
			return

		eons.util.BlackMagick.InjectIntoModule(
			this.function,
			this.error.subject,
			sys.modules[this.error.subject]
		)
		this.error.resolution.successful = True
