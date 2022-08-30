import os
import logging
from eons import UserFunctor


# Class name is what is used at cli, so we defy convention here in favor of ease-of-use.
class hello_world(UserFunctor):
    def __init__(this, name="Hello World"):
        super().__init__(name)

        this.clearBuildPath = False
        this.supportedProjectTypes = []

    # Required UserFunctor method. See that class for details.
    def DidUserFunctionSucceed(this):
        return True 

    # Required UserFunctor method. See that class for details.
    def UserFunction(this, **kwargs):
        print("Hello world!")