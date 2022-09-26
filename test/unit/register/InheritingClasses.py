import sys, os, logging
import eons

class inheritance_positive_control(eons.Datum):
    def __init__(this, name="Inheritance Positive Control"):
        super().__init__(name)

# resolve_install_from_repo.py is included in eons and should always be available.
# from resolve_install_from_repo import install_from_repo
class inheriting_error_resolution(eons.Datum):
    def __init__(this, name="Inheriting Error Resolution"):
        super().__init__(name)

# Assume we are running in a virtual environment or on a fresh vm.
# There is no good reason why the downstream apie package should be installed at this point.
# So, let's try importing it and see if our install_with_pip handler makes it work!
# NOTE: apie is magically instantiated behind the scenes. This may affect testing, since apie is an eons.Executor.
# There's not much I could find on this behavior; from what I can tell it has no need to exists but is done for convinience?
# Here's a possibly relevant article: https://stackoverflow.com/questions/11974848/does-python-import-instantiate-a-mystery-class
import apie
class inheriting_endpoint(apie.Endpoint):
    def __init__(this, name="Inheriting Endpoint"):
        super().__init__(name)

