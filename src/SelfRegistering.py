import os, sys
import logging
import pkgutil
import importlib.machinery
import importlib.util
import types
from .Exceptions import *
from .Namespace import Namespace, NamespaceTracker

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
		logging.debug(f"Creating new {toNew.__name__} from {toNew.__module__}")

		# Using "object" base class method avoids recursion here.
		child = object.__new__(toNew)

		#__dict__ is always blank during __new__ and only populated by __init__.
		#This is only useful as a negative control.
		# logging.debug(f"Created object of {child.__dict__}")

		return child

	# Registering classes is typically depth-first.
	@staticmethod
	def RegisterAllClassesInDirectory(directory, recurse=True, elder=None):
		logging.debug(f"Loading SelfRegistering classes in {directory}")
		directoryContents = [i for i in sorted(os.listdir(directory)) if not i.startswith('_')]

		directories = [i for i in directoryContents if os.path.isdir(os.path.join(directory, i))]
		files = [i for i in directoryContents if os.path.isfile(os.path.join(directory, i))]
		pyFiles = [f for f in files if f.endswith('.py')]
		ldrFiles = [f for f in files if f.endswith('.ldr')]

		if (recurse):
			for dir in directories:				
				SelfRegistering.RegisterAllClassesInDirectory(os.path.join(directory, dir), recurse, elder)

		if (len(pyFiles)):
			SelfRegistering.RegisterPythonFiles(directory, pyFiles)

		if (len(ldrFiles) and elder):
			SelfRegistering.RegisterElderFiles(directory, ldrFiles, elder)

		# enable importing and inheritance for SelfRegistering classes
		if (directory not in sys.path):
			sys.path.append(directory)


	@staticmethod
	def RegisterPythonFiles(directory, files):
		logging.debug(f"Available modules: {files}")
		for file in files:
			moduleName = file.split('.')[0]

			# logging.debug(f"Attempting to registering classes in {moduleName}.")
			loader = importlib.machinery.SourceFileLoader(moduleName, os.path.join(directory, file))
			module = types.ModuleType(loader.name)
			loader.exec_module(module)

			# Mangle the module name to include the namespace.
			# The namespace is set when exec'ing the module, so we'll reset it after.
			importName = NamespaceTracker.Instance().last.ToName() + moduleName
			NamespaceTracker.Instance().last = Namespace()

			setattr(module, '_source', os.path.join(directory, file))

			# NOTE: the module is not actually imported in that it is available through sys.modules.
			# However, this appears to be enough to get both inheritance and SelfRegistering functionality to work.
			module.__imported_as__ = importName
			sys.modules[importName] = module #But just in case...
			logging.debug(f"{moduleName} imported as {importName}.")

			#### Other Options ####
			# __import__(module)
			# OR
			# for importer, module, _ in pkgutil.iter_modules([directory]):
			#	 importer.find_module(module).exec_module(module) #fails with "AttributeError: 'str' object has no attribute '__name__'"
			#	 importer.find_module(module).load_module(module) #Deprecated


	@staticmethod
	def RegisterElderFiles(directory, files, elder):
		logging.debug(f"Elder scripts: {files}")
		for file in files:
			# This should be enough.
			elder.ExecuteLDR(os.path.join(directory, file))