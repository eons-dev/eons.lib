import logging
from abc import ABC, abstractmethod
from .Constants import *
from .Datum import Datum
from .Errors import *

#UserFunctor is a base class for any function-oriented data structure or operation.
#This class derives from Datum, primarily, to give it a name but also to allow it to be stored and manipulated, should you so desire.
class UserFunctor(ABC, Datum):

    def __init__(self, name=INVALID_NAME):
        super().__init__(name)
        self.requiredKWArgs = []

    #Override this and do whatever!
    #This is purposefully vague.
    @abstractmethod
    def UserFunction(self, **kwargs):
        raise NotImplementedError 

    #Override this with any additional argument validation you need.
    #This is called before PreCall(), below.
    def ValidateArgs(self, **kwargs):
        for rkw in self.requiredKWArgs:
            if (rkw not in kwargs):
                raise MissingArgumentError(f"argument \"{rkw}\" not found in {kwargs}")

    #Override this with any logic you'd like to run at the top of __call__
    def PreCall(self, **kwargs):
        pass

    #Override this with any logic you'd like to run at the bottom of __call__
    def PostCall(self, **kwargs):
        pass

    #Make functor.
    #Don't worry about this; logic is abstracted to UserFunction
    def __call__(self, **kwargs) :
        logging.debug(f"{self.name}({kwargs})")
        self.ValidateArgs(**kwargs)
        self.PreCall(**kwargs)
        ret = self.UserFunction(**kwargs)
        self.PostCall(**kwargs)
        return ret
