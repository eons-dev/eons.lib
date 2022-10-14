import sys, os, logging
import eons

class inheritance_positive_control(eons.Datum):
	def __init__(this, name="Inheritance Positive Control"):
		super().__init__(name)

# resolve_install_from_repo.py is included in eons and should always be available.
from resolve_install_from_repo import install_from_repo
class inheriting_error_resolution(install_from_repo):
	def __init__(this, name="Inheriting Error Resolution"):
		super().__init__(name)

# Assume we are running in a virtual environment or on a fresh vm.
# There is no good reason why the downstream pipeadapter package should be installed at this point.
# So, let's try importing it and see if our install_with_pip handler makes it work!
#
# NOTE: import statements seem to magically instantiate their objects behind the scenes.
# This may affect testing, since ehw is an eons.Executor.
# There's not much I could find on this behavior; from what I can tell it has no need to exists and is only done for convenience?
# Here's a possibly relevant article: https://stackoverflow.com/questions/11974848/does-python-import-instantiate-a-mystery-class
# When using 'import apie', calling executor.RegisterAllClassesInDirectory(registerPath) made executor.GetRegistered("test", "package") fail. I have no idea why. Pipeadapter seems to work though.
import ehw
class inheriting_external(ehw.Routine):
	def __init__(this, name="Inheriting External"):
		super().__init__(name)
