import os
import logging
import eons as e

######## START CONTENT ########

class TESTEXECUTOR(e.Executor):

    def __init__(this):

        super().__init__(name="test executor", descriptionStr="TESTING ONLY")

    #Override of eons.Executor method. See that class for details
    def Configure(this):
        super().Configure()

    #Override of eons.Executor method. See that class for details
    def UserFunction(this, **kwargs):
        super().UserFunction(**kwargs)
        hello = this.GetRegistered("hello_world", "functor")
        hello(executor=this)

