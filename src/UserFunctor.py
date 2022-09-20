import logging
import shutil
import traceback
import platform
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from abc import ABC, abstractmethod
from .Constants import *
from .Datum import Datum
from .Errors import *

#UserFunctor is a base class for any function-oriented class structure or operation.
#This class derives from Datum, primarily, to give it a name but also to allow it to be stored and manipulated, should you so desire.
class UserFunctor(ABC, Datum):

    def __init__(this, name=INVALID_NAME()):
        super().__init__(name)

        #All necessary args that *this cannot function without.
        this.requiredKWArgs = []

        #For optional args, supply the arg name as well as a default value.
        this.optionalKWArgs = {}

        #All external dependencies *this relies on (binaries that can be found in PATH).
        this.requiredPrograms = []

        #For converting config value names.
        #e.g. "type": "projectType" makes it so that when calling Set("projectType", ...),  this.type is changed.
        this.configNameOverrides = {}

        #Rolling back can be disabled by setting this to False.
        this.enableRollback = True

        #Numerical result indication the success or failure of *this.
        #Set automatically.
        #0 is invalid; 1 is best; higher numbers are usually worse.
        this.result = 0

        #Whether or not we should pass on exceptions when calls fail.
        this.raiseExceptions = True

        #Ease of use members
        #These can be calculated in UserFunction and Rollback, respectively.
        this.functionSucceeded = False
        this.rollbackSucceeded = False

    #Override this and do whatever!
    #This is purposefully vague.
    @abstractmethod
    def UserFunction(this):
        raise NotImplementedError 

    # Undo any changes made by UserFunction.
    # Please override this too!
    def Rollback(this):
        pass

    #Override this to check results of operation and report on status.
    #Override this to perform whatever success checks are necessary.
    def DidUserFunctionSucceed(this):
        return this.functionSucceeded

    #RETURN whether or not the Rollback was successful.
    #Override this to perform whatever success checks are necessary.
    def DidRollbackSucceed(this):
        return this.rollbackSucceeded

    #Grab any known and necessary args from this.kwargs before any Fetch calls are made.
    def ParseInitialArgs(this):
        this.os = platform.system()
        if (not isinstance(this, Executor)):
            if ('executor' in this.kwargs):
                this.executor = this.kwargs.pop('executor')
            else:
                logging.warning(f"{this.name} was not given an 'executor'. Some features will not be available.")

    # Convert Fetched values to their proper type.
    # This can also allow for use of {this.val} expression evaluation.
    def EvaluateToType(this, value, evaluateExpression = False):
        if (value is None or value == "None"):
            return None

        if (isinstance(value, dict)):
            ret = {}
            for key, value in value.items():
                ret[key] = this.EvaluateToType(value)
            return ret

        elif (isinstance(value, list)):
            ret = []
            for value in value:
                ret.append(this.EvaluateToType(value))
            return ret

        else:
            if (evaluateExpression):
                evaluatedvalue = eval(f"f\"{value}\"")
            else:
                evaluatedvalue = str(value)

            #Check original type and return the proper value.
            if (isinstance(value, (bool, int, float)) and evaluatedvalue == str(value)):
                return value

            #Check resulting type and return a casted value.
            #TODO: is there a better way than double cast + comparison?
            if (evaluatedvalue.lower() == "false"):
                return False
            elif (evaluatedvalue.lower() == "true"):
                return True

            try:
                if (str(float(evaluatedvalue)) == evaluatedvalue):
                    return float(evaluatedvalue)
            except:
                pass

            try:
                if (str(int(evaluatedvalue)) == evaluatedvalue):
                    return int(evaluatedvalue)
            except:
                pass

            #The type must be a string.
            return evaluatedvalue

    # Wrapper around setattr
    def Set(this, varName, value):
        value = this.EvaluateToType(value)
        for key, var in this.configNameOverrides.items():
            if (varName == key):
                varName = var
                break
        logging.debug(f"Setting ({type(value)}) {varName} = {value}")
        setattr(this, varName, value)


    # Will try to get a value for the given varName from:
    #    first: this
    #    second: the local config file
    #    third: the executor (args > config > environment)
    # RETURNS the value of the given variable or default.
    def Fetch(this,
        varName,
        default=None,
        enableThis=True,
        enableExecutor=True,
        enableArgs=True,
        enableExecutorConfig=True,
        enableEnvironment=True):

        if (enableThis and hasattr(this, varName)):
            logging.debug(f"...got {varName} from self ({this.name}).")
            return getattr(this, varName)

        if (enableArgs):
            for key, val in this.kwargs.items():
                if (key == varName):
                    logging.debug(f"...got {varName} from argument.")
                    return val

        if (not hasattr(this, 'executor')):
            logging.debug(f"... skipping remaining Fetch checks, since 'executor' was not supplied in this.kwargs.")
            return default

        return this.executor.Fetch(varName, default, enableExecutor, enableArgs, enableExecutorConfig, enableEnvironment)
        

    #Override this with any additional argument validation you need.
    #This is called before PreCall(), below.
    def ValidateArgs(this):
        # logging.debug(f"this.kwargs: {this.kwargs}")
        # logging.debug(f"required this.kwargs: {this.requiredKWArgs}")

        for prog in this.requiredPrograms:
            if (shutil.which(prog) is None):
                errStr = f"{prog} required but not found in path."
                logging.error(errStr)
                raise BuildError(errStr)

        for rkw in this.requiredKWArgs:
            if (hasattr(this, rkw)):
                continue

            fetched = this.Fetch(rkw)
            if (fetched is not None):
                this.Set(rkw, fetched)
                continue

            # Nope. Failed.
            errStr = f"{rkw} required but not found."
            logging.error(errStr)
            raise MissingArgumentError(f"argument {rkw} not found in {this.kwargs}") #TODO: not formatting string??

        for okw, default in this.optionalKWArgs.items():
            if (hasattr(this, okw)):
                continue

            this.Set(okw, this.Fetch(okw, default=default))

    #Override this with any logic you'd like to run at the top of __call__
    def PreCall(this):
        pass

    #Override this with any logic you'd like to run at the bottom of __call__
    def PostCall(this):
        pass

    #Make functor.
    #Don't worry about this; logic is abstracted to UserFunction
    def __call__(this, **kwargs) :
        logging.debug(f"<---- {this.name} ---->")

        this.kwargs = kwargs
        
        logging.debug(f"{this.name}({this.kwargs})")

        ret = None
        try:
            this.ParseInitialArgs()
            this.ValidateArgs()
            this.PreCall()
            
            ret = this.UserFunction()

            if (this.DidUserFunctionSucceed()):
                    this.result = 1
                    logging.info(f"{this.name} successful!")
            elif (this.enableRollback):
                logging.warning(f"{this.name} failed. Attempting Rollback...")
                this.Rollback()
                if (this.DidRollbackSucceed()):
                    this.result = 2
                    logging.info(f"Rollback succeeded. All is well.")
                else:
                    this.result = 3
                    logging.error(f"Rollback FAILED! SYSTEM STATE UNKNOWN!!!")
            else:
                this.result = 4
                logging.error(f"{this.name} failed.")
            
            this.PostCall()

        except Exception as error:
            if (this.raiseExceptions):
                raise error
            else:
                logging.error(f"ERROR: {error}")
                traceback.print_exc()

        if (this.raiseExceptions and this.result > 2):
            raise UserFunctorError(f"{this.name} failed with result {this.result}")

        logging.debug(f">---- {this.name} complete ----<")
        return ret

    ######## START: UTILITIES ########

    #RETURNS: an opened file object for writing.
    #Creates the path if it does not exist.
    def CreateFile(this, file, mode="w+"):
        Path(os.path.dirname(os.path.abspath(file))).mkdir(parents=True, exist_ok=True)
        return open(file, mode)

    #Copy a file or folder from source to destination.
    #This really shouldn't be so hard...
    #root allows us to interpret '/' as something other than the top of the filesystem.
    def Copy(this, source, destination, root='/'):
        if (source.startswith('/')):
            source = str(Path(root).joinpath(source[1:]).resolve())
        else:
            source = str(Path(source).resolve())
        
        destination = str(Path(destination).resolve())
        
        Path(os.path.dirname(os.path.abspath(destination))).mkdir(parents=True, exist_ok=True)

        if (os.path.isfile(source)):
            logging.debug(f"Copying file {source} to {destination}")
            try:
                shutil.copy(source, destination)
            except shutil.Error as exc:
                errors = exc.args[0]
                for error in errors:
                    src, dst, msg = error
                    logging.debug(f"{msg}")
        elif (os.path.isdir(source)):
            logging.debug(f"Copying directory {source} to {destination}")
            try:
                shutil.copytree(source, destination)
            except shutil.Error as exc:
                errors = exc.args[0]
                for error in errors:
                    src, dst, msg = error
                    logging.debug(f"{msg}")
        else:
            logging.error(f"Could not find source to copy: {source}")

    #Delete a file or folder
    def Delete(this, target):
        if (not os.path.exists(target)):
            logging.debug(f"Unable to delete nonexistent target: {target}")
            return
        if (os.path.isfile(target)):
            logging.debug(f"Deleting file {target}")
            os.remove(target)
        elif (os.path.isdir(target)):
            logging.debug(f"Deleting directory {target}")
            try:
                shutil.rmtree(target)
            except shutil.Error as exc:
                errors = exc.args[0]
                for error in errors:
                    src, dst, msg = error
                    logging.debug(f"{msg}")

    #Run whatever.
    #DANGEROUS!!!!!
    #RETURN: Return value and, optionally, the output as a list of lines.
    #per https://stackoverflow.com/questions/803265/getting-realtime-output-using-subprocess
    def RunCommand(this, command, saveout=False, raiseExceptions=True):
        logging.debug(f"================ Running command: {command} ================")
        p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        output = []
        while p.poll() is None:
            line = p.stdout.readline().decode('utf8')[:-1]
            if (saveout):
                output.append(line)
            if (line):
                logging.debug(f"| {line}")  # [:-1] to strip excessive new lines.

        if (p.returncode is not None and p.returncode):
            raise CommandUnsuccessful(f"Command returned {p.returncode}")
        
        logging.debug(f"================ Completed command: {command} ================")
        if (saveout):
            return p.returncode, output
        
        return p.returncode
    ######## END: UTILITIES ########
