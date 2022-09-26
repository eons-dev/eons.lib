import logging
from eons import UserFunctor

class test(UserFunctor):
    def __init__(this, name="Test Package"):
        super().__init__(name)
    
    def UserFunction(this, **kwargs):
        logging.info("Test functor successfully executed")
        this.functionSucceeded = True
