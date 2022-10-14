import re
import logging
import traceback
from .Constants import *
from .Exceptions import *
from .StandardFunctor import StandardFunctor


# Use an ErrorStringParser for each "parsers" in order to avoid having to override the GetObjectFromError method and create a new class for every error you want to handle.
# ErrorStringParsers enable ErrorResolutions to be created on a per-functionality, rather than per-error basis, reducing the total amount of duplicate code.
# Each error has a different string. In order to get the object of the error, we have to know where the object starts and ends.
# NOTE: this assumes only 1 object per string. Maybe fancier parsing logic can be added in the future.
#
# startPosition is always positive
# endPosition is always negative
class ErrorStringParser:

	def __init__(this, applicableError, startPosition, endPosition):
		this.applicableError = applicableError
		this.startPosition = startPosition
		this.endPosition = endPosition

	def Parse(this, errorString):
		end = this.endPosition
		if (not end):
			end = len(errorString)
		return errorString[this.startPosition:end]


# ErrorResolution is a Functor which can be executed when an Exception is raised.
# The goal of this class is to do some kind of work that will fix the problem on the second try of whatever generated the error.
class ErrorResolution(StandardFunctor):

	def __init__(this, name=INVALID_NAME()):
		super().__init__(name)

		# What errors, as ErrorStringParser objects, is *this prepared to handle?
		this.parsers = []

		this.error = None
		this.errorType = ""
		this.errorString = ""
		this.errorObject = ""
		this.errorResolutionStack = {}

		# We do want to know whether or not we should attempt to run whatever failed again.
		# So, let's store that in functionSucceeded. Meaning if this.functionSucceeded, try the original method again.
		# No rollback, by default and definitely don't throw Exceptions.
		this.enableRollback = False
		this.functionSucceeded = True
		this.raiseExceptions = False

		this.errorShouldBeResolved = False



	# Put your logic here!
	def Resolve(this):
		# You get the following members:
		# this.error (an Exception)
		# this.errorString (a string cast of the Exception)
		# this.errorType (a string)
		# this.errorObjet (a string or whatever you return from GetObjectFromError())

		# You get the following guarantees:
		# *this has not been called on this particular error before.
		# the error given is applicable to *this per this.parsers

		###############################################
		# Please throw errors if something goes wrong #
		# Otherwise, set this.errorShouldBeResolved   #
		###############################################
		
		pass



	# Helper method for creating ErrorStringParsers
	# To use this, simply take an example output and replace the object you want to extract with "OBJECT"
	def ApplyTo(this, error, exampleString):
		match = re.search('OBJECT', exampleString)
		this.parsers.append(ErrorStringParser(error, match.start(), match.end() - len(exampleString)))


	# Get the type of this.error as a string.
	def GetErrorType(this):
		return type(this.error).__name__


	# Get an actionable object from the error.
	# For example, if the error is 'ModuleNotFoundError', what is the module?
	def GetObjectFromError(this):
		for parser in this.parsers:
			if (parser.applicableError != this.errorType):
				continue

			this.errorObject = parser.Parse(this.errorString)
			return

		raise ErrorResolutionError(f"{this.name} cannot parse error object from ({this.errorType}): {str(this.error)}.")


	# Determine if this resolution method is applicable.
	def CanProcess(this):
		return this.GetErrorType() in [parser.applicableError for parser in this.parsers]


	# Grab any known and necessary args from this.kwargs before any Fetch calls are made.
	def ParseInitialArgs(this):
		super().ParseInitialArgs()
		if ('error' in this.kwargs):
			this.error = this.kwargs.pop('error')
			# Just assume the error is an actual Exception object.
		else:
			raise ErrorResolutionError(f"{this.name} was not given an error to resolve.")

		this.errorString = str(this.error)
		this.errorType = this.GetErrorType()

		# Internal member to avoid processing duplicates
		this.errorResolutionStack = this.executor.errorResolutionStack


	# Error resolution is unchained.
	def PopulateNext(this):
		this.next = []


	# Override of Functor method.
	# We'll keep calling this until an error is raised.
	def Function(this):
		this.functionSucceeded = True
		this.errorShouldBeResolved = True
		
		if (not this.CanProcess()):
			this.errorShouldBeResolved = False
			return this.errorResolutionStack, this.errorShouldBeResolved

		if (not this.errorString in this.errorResolutionStack.keys()):
			this.errorResolutionStack.update({this.errorString:[]})
		
		if (this.name in this.errorResolutionStack[this.errorString]):
			raise FailedErrorResolution(f"{this.name} already tried and failed to resolve {this.errorType}: {this.errorString}.")

		this.GetObjectFromError()

		try:
			this.Resolve()
		except Exception as e:
			logging.error(f"Error resolution with {this.name} failed: {e}")
			if (this.executor.parsedArgs.verbose > 0 and this.executor.parsedArgs.quiet == 0):
				traceback.print_exc()
			this.functionSucceeded = False
		
		this.errorResolutionStack[this.errorString].append(this.name)
		return this.errorResolutionStack, this.errorShouldBeResolved
