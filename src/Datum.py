import logging
from .Constants import *
from .SelfRegistering import SelfRegistering

# A Datum is a base class for any object-oriented class structure.
# This class is intended to be derived from and added to.
# The members of this class are helpful labels along with the ability to invalidate a datum.
class Datum(SelfRegistering):

	# Don't worry about this.
	# If you really want to know, look at SelfRegistering.
	def __new__(cls, *args, **kwargs):
		return object.__new__(cls)


	def __init__(this, name=INVALID_NAME(), number=0):
		# logging.debug("init Datum")

		# Names are generally useful.
		this.name = name

		# Storing validity as a member makes it easy to generate bad return values (i.e. instead of checking for None) as well as manipulate class (e.g. each analysis step invalidates some class and all invalid class are discarded at the end of analysis).
		this.valid = True

	# Override this if you have your own validity checks.
	def IsValid(this):
		return this.valid == True


	# Sets valid to true
	# Override this if you have members you need to handle with care.
	def MakeValid(this):
		this.valid = True


	# Sets valid to false.
	def Invalidate(this):
		this.valid = False
