import re
import logging
from .Constants import *
from .Exceptions import *
from .StandardFunctor import StandardFunctor
from .Utils import util

# Use an ErrorStringParser for each "parsers" in order to avoid having to override the GetSubjectFromError method and create a new class for every error you want to handle.
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

		this.error = util.DotDict()
		this.error.object = None
		this.error.type = ""
		this.error.string = ""
		this.error.subject = ""
		this.error.resolution = util.DotDict()
		this.error.resolution.successful = False
		this.error.resolution.stack = {}

		# Provided directly from the recoverable decorator.
		this.arg.kw.optional["obj"] = None
		this.arg.kw.optional["function"] = None

		# We do want to know whether or not we should attempt to run whatever failed again.
		# So, let's store that in functionSucceeded. Meaning if this.functionSucceeded, try the original method again.
		# No rollback, by default and definitely don't throw Exceptions.
		this.feature.rollback = False
		this.feature.raiseExceptions = False
		this.feature.autoReturn = False
		this.functionSucceeded = True

		this.functionSucceeded = True

	# Put your logic here!
	def Resolve(this):
		# You get the following members:
		# this.error (an Exception)
		# this.error.string (a string cast of the Exception)
		# this.error.type (a string)
		# this.error.subject (a string or whatever you return from GetSubjectFromError())

		# You get the following guarantees:
		# *this has not been called on this particular error before.
		# the error given is applicable to *this per this.parsers

		###############################################
		# Please throw errors if something goes wrong #
		# Otherwise, set this.error.resolution.successful   #
		###############################################
		
		pass



	# Helper method for creating ErrorStringParsers
	# To use this, simply take an example output and replace the object you want to extract with "SUBJECT"
	def ApplyTo(this, error, exampleString):
		match = re.search('SUBJECT', exampleString)
		this.parsers.append(ErrorStringParser(error, match.start(), match.end() - len(exampleString)))


	# Get the type of this.error as a string.
	def GetErrorType(this):
		return type(this.error).__name__


	# Get an actionable object from the error.
	# For example, if the error is 'ModuleNotFoundError', what is the module?
	def GetSubjectFromError(this):
		for parser in this.parsers:
			if (parser.applicableError != this.error.type):
				continue

			this.error.subject = parser.Parse(this.error.string)
			return

		raise ErrorResolutionError(f"{this.name} cannot parse error object from ({this.error.type}): {str(this.error)}.")


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

		this.error.string = str(this.error)
		this.error.type = this.GetErrorType()

		# Internal member to avoid processing duplicates
		this.error.resolution.stack = this.executor.error.resolution.stack


	# Error resolution is unchained.
	def PopulateNext(this):
		this.next = []


	# Override of Functor method.
	# We'll keep calling this until an error is raised.
	def Function(this):
		this.functionSucceeded = True
		this.error.resolution.successful = True
		
		if (not this.CanProcess()):
			this.error.resolution.successful = False
			return this.error.resolution.stack, this.error.resolution.successful

		if (not this.error.string in this.error.resolution.stack.keys()):
			this.error.resolution.stack.update({this.error.string:[]})
		
		if (this.name in this.error.resolution.stack[this.error.string]):
			raise FailedErrorResolution(f"{this.name} already tried and failed to resolve {this.error.type}: {this.error.string}.")

		this.GetSubjectFromError()

		try:
			this.Resolve()
		except Exception as e:
			logging.error(f"Error resolution with {this.name} failed: {e}")
			util.LogStack()
			this.functionSucceeded = False
		
		this.error.resolution.stack[this.error.string].append(this.name)
		return this.error.resolution.stack, this.error.resolution.successful
