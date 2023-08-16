import eons
import inspect
import logging
# import re
import builtins

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
	def __init__(this, name="find_by_fetch"):
		super().__init__(name)

		this.ApplyTo('NameError', "name 'SUBJECT' is not defined")

	def Resolve(this):
		# Using builtins works. This logic has been moved to Executor.
		# See below for a couple other ways this could be accomplished.
		this.executor.SetGlobalFromFetch(this.error.subject)
		this.error.resolution.successful = eons.util.HasAttr(builtins, this.error.subject)

		# This method of modifying the function's source code is a potential alternative to global variables.
		# However, it can be dangerous or just not work.
		# And, if we got a NameError, we know there is no global of that name, so defining a new global should always be safe.
		# This method of hacking the function's source also only works for the current function, whereas a global potentially keeps us from having to come back here again for another function.
		# Lastly, it's far easier to keep track of what globals we've put where than which functions we've hacked and how. So, if we want to update the value of what we've Fetched here, globals are the way to go.
		#
		# # Get the source code of the erroring function.
		# source = inspect.getsource(this.function)
		#
		# # Remove any extra indents from it.
		# indent = source[0:len(source) - len(source.lstrip())]
		# sourceMod = re.sub(fr"{indent}({indent}*)", r"\1", source)
		#
		# # Separate the declaration from the definition
		# decl = ':'.join(sourceMod.split(':')[0])
		# defin = ':'.join(sourceMod.split(':')[1:])
		#
		# # Add the new declaration to the top of the function
		# defin = f"\n{indent}{this.error.subject} = {value}{defin}"
		#
		# # Bring it all back together
		# sourceMod = decl + defin
		# if (this.executor.verbosity > 3):
		# 	logging.debug(f"Modified source for {this.function.__name__} is:\n{sourceMod}")
		#
		# # Now, in order to compile, we'll need the same imports as wherever that function came from.
		# # ...
		#
		# # Compile the new function!
		# code = compile(sourceMod, 'string', 'exec')
		# this.function.__code__ = code

		# Global variables in python are module scoped.
		# So, we have to get the module of the erroring function and add a global variable to that.
		# This does what it's supposed to but somehow doesn't update globals() in the other module, leaving the module's __dict__ and globals() entirely identical EXCEPT for the value that we want.
		#
		# moduleToHack = inspect.getmodule(this.function)
		# setattr(moduleToHack, this.error.subject, value)
