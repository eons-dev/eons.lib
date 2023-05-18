import traceback
import logging
import jsonpickle
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

	# DotDict doesn't pickle right, since it's a class and not a native dict.
	class DotDictPickler(jsonpickle.handlers.BaseHandler):
		def flatten(this, dotdict, data):
			return dict(dotdict)

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


	class console:

		# Read this (just do it): https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences

		saturationCode = {
			'dark': 3,
			'light': 9
		}

		foregroundCodes = {
			'black': 0,
			'red': 1,
			'green': 2,
			'yellow': 3,
			'blue': 4,
			'magenta': 5,
			'cyan': 6,
			'white': 7
		}

		backgroundCodes = {
			'none': 0,
			'black': 40,
			'red': 41,
			'green': 42,
			'yellow': 43,
			'blue': 44,
			'magenta': 45,
			'cyan': 46,
			'white': 47,
		}

		styleCodes = {
			'none': 0,
			'bold': 1,
			'faint': 2, # Not widely supported.
			'italic': 3, # Not widely supported.
			'underline': 4,
			'blink_slow': 5,
			'blink_fast': 6, # Not widely supported.
			'invert': 7,
			'conceal': 8, # Not widely supported.
			'strikethrough': 9, # Not widely supported.
			'frame': 51,
			'encircle': 52,
			'overline': 53
		}

		@classmethod
		def GetColorCode(cls, foreground, saturation='dark', background='none', styles=None):
			if (styles is None):
				styles = []
			#\x1b may also work.
			compiledCode = f"\033[{cls.saturationCode[saturation]}{cls.foregroundCodes[foreground]}"
			if (background != 'none'):
				compiledCode += f";{cls.backgroundCodes[background]}"
			if (styles):
				compiledCode += ';' + ';'.join([str(cls.styleCodes[s]) for s in list(styles)])
			compiledCode += 'm'
			return compiledCode

		resetStyle = "\033[0m"


	# Add a logging level
	# per: https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
	@staticmethod
	def AddLoggingLevel(level, value):
		levelName = level.upper()
		methodName = level.lower()

		if hasattr(logging, levelName):
			raise AttributeError('{} already defined in logging module'.format(levelName))
		if hasattr(logging, methodName):
			raise AttributeError('{} already defined in logging module'.format(methodName))
		if hasattr(logging.getLogger(), methodName):
			raise AttributeError('{} already defined in logger class'.format(methodName))

		# This method was inspired by the answers to Stack Overflow post
		# http://stackoverflow.com/q/2183233/2988730, especially
		# http://stackoverflow.com/a/13638084/2988730
		def logForLevel(this, message, *args, **kwargs):
			if this.isEnabledFor(value):
				this._log(value, message, args, **kwargs)
		def logToRoot(message, *args, **kwargs):
			logging.log(value, message, *args, **kwargs)

		logging.addLevelName(value, levelName)
		setattr(logging, levelName, value)
		setattr(logging.getLogger(), methodName, logForLevel)
		setattr(logging, methodName, logToRoot)


jsonpickle.handlers.registry.register(util.DotDict, util.DotDictPickler)
