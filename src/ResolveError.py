from .UserFunctor import UserFunctor
from .Constants import *
from .Exceptions import *
import re


#Use an ErrorStringParser for each "parsers" in order to avoid having to override the GetObjectFromError method and create a new class for every error you want to handle.
#ErrorStringParsers enable ResolveErrors to be created on a per-functionality, rather than per-error basis, reducing the total amount of duplicate code.
#Each error has a different string. In order to get the object of the error, we have to know where the object starts and ends.
#NOTE: this assumes only 1 object per string. Maybe fancier parsing logic can be added in the future.
#
#startPosition is always positive
#endPosition is always negative
class ErrorStringParser:
    def __init__(this, applicableError, startPosition, endPosition):
        this.applicableError = applicableError
        this.startPosition = startPosition
        this.endPosition = endPosition

    def Parse(errorString):
        return errorString[this.startPosition, this.endPosition]


#ResolveError is a UserFunctor which can be executed when an Exception is raised.
#The goal of this class is to do some kind of work that will fix the problem on the second try of whatever generated the error.
class ResolveError(UserFunctor):

    def __init__(this, name=INVALID_NAME()):
        super().__init__(name)

        #What errors, as ErrorStringParser objects, is *this prepared to handle?
        this.parsers = []

        this.error = None
        this.errorType = ""
        this.errorString = ""
        this.errorObject = ""
        this.errorResolutionStack = {}

        #We'll raise exceptions if something goes wrong. No need for clean handling.
        this.enableRollback = False
        this.functionSucceeded = True


    #Put your logic here!
    def Resolve(this):
        #You get the following members:
        # this.error (an Exception)
        # this.errorString (a string cast of the Exception)
        # this.errorType (a string)
        # this.errorObjet (a string or whatever you return from GetObjectFromError())

        #You get the following guarantees:
        # *this has not been called on this particular error before.
        # the error given is applicable to *this per this.parsers
        pass



    #Helper method for creating ErrorStringParsers
    #To use this, simply take an example output and replace the object you want to extract with "OBJECT"
    def ApplyTo(this, error, exampleString):
        match = re.search('OBJECT', exampleString)
        this.parsers.append(ErrorStringParser(error, match.start(), match.end() - len(exampleString)))

    #Get the type of this.error as a string.
    def GetErrorType(this):
        return type(this.error).__name__

    #Get an actionable object from the error.
    #For example, if the error is 'ModuleNotFoundError', what is the module?
    def GetObjectFromError(this):
        for parser in this.parsers:
            if (parser.applicableError != this.errorType):
                continue
            end = parser.endPosition
            if (not end):
                end = len(this.errorString)
            this.errorObject = this.errorString[parser.startPosition:end]
            return
        raise ErrorResolutionError(f"{this.name} cannot parse error object from ({this.errorType}): {str(this.error)}.")

    #Determine if this resolution method is applicable.
    def CanProcess(this):
        return this.GetErrorType() in [parser.applicableError for parser in this.parsers]

    #Grab any known and necessary args from this.kwargs before any Fetch calls are made.
    def ParseInitialArgs(this):
        super().ParseInitialArgs()
        if ('error' in this.kwargs):
            this.error = this.kwargs.pop('error')
            #Just assume the error is an actual Exception object.
        else:
            raise ErrorResolutionError(f"{this.name} was not given an error to resolve.")

        this.errorString = str(this.error)
        this.errorType = this.GetErrorType()

        #Internal member to avoid processing duplicates
        this.errorResolutionStack = this.executor.errorResolutionStack

    #Override of UserFunctor method.
    #We'll keep calling this until an error is raised.
    def UserFunction(this):
        if (not this.CanProcess()):
            return this.errorResolutionStack

        if (not this.error in this.errorResolutionStack.keys()):
            this.errorResolutionStack.update({this.error:[]})
        
        if (this.name in this.errorResolutionStack[this.error]):
            raise FailedErrorResolution(f"{this.name} already tried and failed to resolve {this.errorType}: {str(this.error)}.")

        this.GetObjectFromError()

        this.Resolve()
        
        this.errorResolutionStack[this.error].append(this.name)
        return this.errorResolutionStack
