import traceback
import logging
from .Exceptions import *
from copy import deepcopy

# util is a namespace for any miscellaneous utilities.
# You cannot create a util.
class util:
	def __init__(this):
		raise NotInstantiableError("util is a namespace, not a class; it cannot be instantiated.")

	#dot.notation access to dictionary attributes
	class DotDict(dict):
		__getattr__ = dict.get
		__setattr__ = dict.__setitem__
		__delattr__ = dict.__delitem__

		def __deepcopy__(this, memo=None):
			return util.DotDict(deepcopy(dict(this), memo=memo))


	@staticmethod
	def RecursiveAttrFunc(func, obj, attrList):
		attr = attrList.pop(0)
		if (not attrList):
			return eval(f"{func}attr(obj, attr)")
		if (not hasattr(obj, attr)):
			raise AttributeError(f"{obj} has not attribute '{attr}'")
		return util.RecursiveAttrFunc(func, getattr(obj, attr), attrList)

	@staticmethod
	def HasAttr(obj, attrStr):
		return util.RecursiveAttrFunc('has', obj, attrStr.split('.'))

	@staticmethod
	def GetAttr(obj, attrStr):
		return util.RecursiveAttrFunc('get', obj, attrStr.split('.'))

	@staticmethod
	def SetAttr(obj, attrStr):
		raise NotImplementedError(f"util.SetAttr has not been implemented yet.")


	@staticmethod
	def LogStack():
		logging.debug(traceback.format_exc())
