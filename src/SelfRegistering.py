import os, sys
import logging
import pkgutil
from .Exceptions import *

#Self registration for use with json loading.
#Any class that derives from SelfRegistering can be instantiated with:
#   SelfRegistering("ClassName")
#Based on: https://stackoverflow.com/questions/55973284/how-to-create-this-registering-factory-in-python/55973426
class SelfRegistering(object):

    class ClassNotFound(Exception): pass

    def __init__(this, *args, **kwargs):
        #ignore args.
        super().__init__()

    @classmethod
    def GetSubclasses(cls):
        for subclass in cls.__subclasses__():
            # logging.info(f"Subclass dict: {subclass.__dict__}")
            yield subclass
            for subclass in subclass.GetSubclasses():
                yield subclass

    @classmethod
    def GetClass(cls, classname):
        for subclass in cls.GetSubclasses():
            if subclass.__name__ == classname:
                return subclass

        # no subclass with matching classname found (and no default defined)
        raise ClassNotFound(f"No known SelfRegistering class: {classname}")            

    #TODO: How do we pass args to the subsequently called __init__()?
    def __new__(cls, classname, *args, **kwargs):
        toNew = cls.GetClass(classname)
        logging.debug(f"Creating new {toNew.__name__}")

        # Using "object" base class method avoids recursion here.
        child = object.__new__(toNew)

        #__dict__ is always blank during __new__ and only populated by __init__.
        #This is only useful as a negative control.
        # logging.debug(f"Created object of {child.__dict__}")

        return child
        
    @staticmethod
    def RegisterAllClassesInDirectory(directory):
        logging.debug(f"Loading SelfRegistering classes in {directory}")
        # logging.debug(f"Available files: {os.listdir(directory)}")
        for importer, file, _ in pkgutil.iter_modules([directory]):
            logging.debug(f"Found {file} with {importer}")
            if (file != 'main'): #ignore check for file not in sys.modules
                importer.find_module(file).load_module(file) #FIXME: Deprecated
                # __import__(file) #FIXME: just doesn't work for 'test'???
                #importer.find_module(file).exec_module(file) #fails with "AttributeError: 'str' object has no attribute '__name__'" ???

        # enable importing and inheritance for SelfRegistering classes
        if (directory not in sys.path):
            sys.path.append(directory)
