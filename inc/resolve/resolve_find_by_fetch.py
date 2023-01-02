import eons
from inspect import getmodule
import logging

# Try to resolve an undefined symbol by fetching it.
# This works by setting a global variable of the name given.
# Unfortunately, this currently means read only access to that variable.
# However, that's okay since the way we implement this, we copy the Fetched value to the relevant module. Thus, any writes would not change the original value and things could get out of sync.
# The above statement applies in reverse, any changes to the original value will not be propagated to subsequent calls to the value we grab here.
#
# WHEN TO USE
# Use this whenever you want to easily read a static config value without writing all the usual code.
#
# For example:
# eons.Fetch('my_var')["some_val"]
# can be written
# my_var.some_val
#
# ILLEGAL: my_var.some_val = "new value"
# OK: local = my_var.some_val
class find_by_fetch(eons.ErrorResolution):
	def __init__(this, name="find_in_config"):
		super().__init__(name)

		this.ApplyTo('NameError', "name 'OBJECT' is not defined")

	def Resolve(this):
		value = None
		isSet = False

		if (this.executor.currentConfigKey):
			config = this.executor.Fetch(this.executor.currentConfigKey)
			if (this.errorObject in config):
				value =  this.executor.EvaluateToType(getattr(config, this.errorObject))
				isSet = True

		if (not isSet):
			val, fetched = this.executor.Fetch(this.errorObject, start=False)
			if (fetched):
				value = this.executor.EvaluateToType(val)
				isSet = True

		if (isSet):
			# In cause the value was accessed with ".", we need to cast it to a DotDict.
			if (isinstance(value, dict)):
				value = eons.util.DotDict(value)

			# Global variables in python are module scoped.
			# So, we have to get the module of the erroring function and add a global variable to that.
			moduleToHack = getmodule(this.function)
			logging.debug(f"Setting {this.errorObject} = {value} in {moduleToHack}")
			setattr(moduleToHack, this.errorObject, value)
			this.errorShouldBeResolved = True
		else:
			this.errorShouldBeResolved = False
