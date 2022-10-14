import os, sys
import logging
import pkgutil
import importlib.machinery
import importlib.util
import types
from .Exceptions import *

#Self registration for use with json loading.
#Any class that derives from SelfRegistering can be instantiated with:
#   SelfRegistering("ClassName")
#Based on: https://stackoverflow.com/questions/55973284/how-to-create-this-registering-factory-in-python/55973426
class SelfRegistering(object):

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
		logging.debug(f"Available modules: {os.listdir(directory)}")
		for file in os.listdir(directory):
			if (file.startswith('_') or not file.endswith('.py')):
				continue

			moduleName = file.split('.')[0]

			# logging.debug(f"Attempting to registering classes in {moduleName}.")
			loader = importlib.machinery.SourceFileLoader(moduleName, os.path.join(directory, file))
			module = types.ModuleType(loader.name)
			loader.exec_module(module)

			# NOTE: the module is not actually imported in that it is available through sys.modules.
			# However, this appears to be enough to get both inheritance and SelfRegistering functionality to work.
			sys.modules[moduleName] = module #But just in case...
			logging.debug(f"{moduleName} imported.")

			#### Other Options ####
			# __import__(module)
			# OR
			# for importer, module, _ in pkgutil.iter_modules([directory]):
			#	 importer.find_module(module).exec_module(module) #fails with "AttributeError: 'str' object has no attribute '__name__'"
			#	 importer.find_module(module).load_module(module) #Deprecated

		# enable importing and inheritance for SelfRegistering classes
		if (directory not in sys.path):
			sys.path.append(directory)
