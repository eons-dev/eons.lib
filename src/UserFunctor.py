import logging
from abc import ABC, abstractmethod
from .Constants import *
from .Datum import Datum
from .Errors import *

#UserFunctor is a base class for any function-oriented class structure or operation.
#This class derives from Datum, primarily, to give it a name but also to allow it to be stored and manipulated, should you so desire.
class UserFunctor(ABC, Datum):

    def __init__(this, name=INVALID_NAME()):
        super().__init__(name)
        this.requiredKWArgs = []

    #Override this and do whatever!
    #This is purposefully vague.
    @abstractmethod
    def UserFunction(this, **kwargs):
        raise NotImplementedError 

    #Override this with any additional argument validation you need.
    #This is called before PreCall(), below.
    def ValidateArgs(this, **kwargs):
        logging.debug(f"kwargs: {kwargs}")
        logging.debug(f"required kwargs: {this.requiredKWArgs}")
        for rkw in this.requiredKWArgs:
            if (rkw not in kwargs):
                logging.error(f"argument {rkw} not found in {kwargs}")
                raise MissingArgumentError(f"argument {rkw} not found in {kwargs}") #TODO: not formatting string??

    #Override this with any logic you'd like to run at the top of __call__
    def PreCall(this, **kwargs):
        pass

    #Override this with any logic you'd like to run at the bottom of __call__
    def PostCall(this, **kwargs):
        pass

    #Make functor.
    #Don't worry about this; logic is abstracted to UserFunction
    def __call__(this, **kwargs) :
        logging.debug(f"{this.name}({kwargs})")
        this.ValidateArgs(**kwargs)
        this.PreCall(**kwargs)
        ret = this.UserFunction(**kwargs)
        this.PostCall(**kwargs)
        return ret
