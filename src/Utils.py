import logging
from .Exceptions import *

# Ease-of-use method for logging and raising errors at once.
def LogAndRaiseError(this, errorString, errorType):
    logging.error(errorString)
    raise errorType(errorString)