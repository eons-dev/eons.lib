import logging
from eons import UserFunctor

class test(UserFunctor):
    def __init__(self, name="Test Package"):
        super().__init__(name)
    
    def UserFunction(self, **kwargs):
        logging.info("Test functor successfully executed")
        return True
