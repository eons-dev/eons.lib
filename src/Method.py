import inspect
import logging
from .Constants import *
from .Exceptions import *
from .SelfRegistering import SelfRegistering
from .Functor import Functor
from .Utils import util

def GetPendingMethod(methodName):
	def METHOD_PENDING_POPULATION(obj, *args, **kwargs):
		raise MethodPendingPopulation(f"METHOD {methodName} PENDING POPULATION")
	return METHOD_PENDING_POPULATION


# Store the new method in the class
def PrepareClassMethod(cls, name, methodToAdd):
	# There is a potential bug here: if the class derives from a class which already has the classMethods static member, this will add to the PARENT class's classMethods. Thus, 2 classes with different methods will share those methods via their shared parent.
	if (not hasattr(cls, 'classMethods') or not isinstance(cls.classMethods, dict)):
		cls.classMethods = {}
	else:
		# to account for the bug above, shadow classMethods out of the base class & into the derived.
		setattr(cls, 'classMethods', getattr(cls, 'classMethods').copy())

	cls.classMethods[name] = methodToAdd

	# Self-destruct by replacing the decorated function.
	# We rely on Functor.PopulateMethods to re-establish the method as callable.
	# It seems like this just outright removes the methods. There may be an issue with using __get__ this way.
	# Regardless deleting the method is okay as long as we add it back before anyone notices.
	setattr(cls, name, GetPendingMethod(name).__get__(cls))

# Use the @method() decorator to turn any class function into an eons Method Functor.
# Methods are Functors which can be implicitly transferred between classes (see Functor.PopulateMethods)
# Using Methods also gives us full control over the execution of your code; meaning, we can change how Python interprets what you wrote!
# All Methods will be stored in the method member of your Functor. However, you shouldn't need to access that.
#
# If you would like to specify a custom implementation, set the 'impl' kwarg (e.g. @method(impl='MyMethodImplementation'))
# Beside 'impl', all key-word arguments provided to the @method() decorator will be set as member variables of the created Method.
# For example, to set whether or not the Method should be propagated, you can use @method(propagate=True).
# This means, you can create a custom means of interpreting your code with your own feature set and still use this @method decorator.
# Perhaps you'd like something along the lines of: @method(impl='MakeAwesome', awesomeness=10000).
# NOTE: in order for impl to work, the implementation class must already be Registered (or this must be called from an appropriate @recoverable function).
def method(impl='Method', **kwargs):

	# Class decorator with __set_name__, as described here: https://stackoverflow.com/questions/2366713/can-a-decorator-of-an-instance-method-access-the-class
	class MethodDecorator:
		def __init__(this, function):
			this.function = function

		# Apparently, this is called when the decorated function is constructed.
		def __set_name__(this, cls, functionName):
			logging.debug(f"Constructing new method for {this.function} in {cls}")

			# Create and configure a new Method

			methodToAdd = SelfRegistering(impl)
			methodToAdd.Constructor(this.function, cls)
			for key, value in kwargs.items():
				setattr(methodToAdd, key, value)

			PrepareClassMethod(cls, functionName, methodToAdd)

	return MethodDecorator

class Method(Functor):

	def __init__(this, name=INVALID_NAME()):
		super().__init__(name)

		# Methods do not fetch from the environment by default.
		this.fetch.use.remove('environment')

		# Whether or not *this should be combined with other Methods of the same name.
		this.inheritMethods = True

		# Where should inherited methods be inserted?
		# First here means "before *this".
		# If False, inherited code will be run after *this.
		this.inheritedMethodsFirst = True # otherwise ...Last

		# Propagation allows for Functors called after that which defines *this to also call *this.
		# This system allows for partial, implicit inheritance.
		# By default, Methods will not be propagated. Use @propagate to enable propagation.
		this.propagate = False

		# We don't care about these checks right now.
		# Plus, we can't exactly wrap 2 functions even if we wanted to Rollback.
		this.functionSucceeded = True
		this.rollbackSucceeded = True
		this.feature.rollback = False

		# Methods,by default, do not return themselves.
		this.feature.autoReturn = False

		# The source code of the function we're implementing.
		this.source = ""

		this.original = util.DotDict()
		this.original.cls = util.DotDict()
		this.original.cls.object = None
		this.original.cls.name = 'None'
		this.original.function = None

		this.arg.mapping = ['epidef']


	# Make *this execute the code in this.source
	def UpdateSource(this):
		wrappedFunctionName = f'_eons_method_{this.name}'
		completeSource = f'''\
def {wrappedFunctionName}(this):
{this.source}
'''
		if (this.executor and this.executor.verbosity > 3):
			logging.debug(f"Source for {this.name} is:\n{completeSource}")
		code = compile(completeSource, '', 'exec')
		exec(code)
		exec(f'this.Function = {wrappedFunctionName}.__get__(this, this.__class__)')


	# Parse arguments and update the source code
	# TODO: Implement full python parser to avoid bad string replacement (e.g. "def func(self):... self.selfImprovement" => "... this.epidef.this.epidef.Improvement").
	def PopulateFrom(this, function):
		this.source = ':'.join(inspect.getsource(function).split(':')[1:]) #Remove the first function definition

		args = inspect.signature(function, follow_wrapped=False).parameters
		thisSymbol = next(iter(args))
		#del args[thisSymbol] # ??? 'mappingproxy' object does not support item deletion
		this.source = this.source.replace(thisSymbol, 'this.epidef')

		first = True
		for arg in args.values(): #args.values[1:] also doesn't work.
			if (first):
				first = False
				continue

			replaceWith = arg.name

			if (arg.kind == inspect.Parameter.VAR_POSITIONAL):
				replaceWith = 'this.args'

			elif (arg.kind == inspect.Parameter.VAR_KEYWORD):
				replaceWith = 'this.kwargs'

			else:
				if (arg.default != inspect.Parameter.empty):
					this.arg.kw.optional[arg.name] = arg.default
				else:
					this.arg.kw.required.append(arg.name)
				replaceWith = f'this.{arg.name}'

				if (arg.kind in [inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY]):
					this.arg.mapping.append(arg.name)

			this.source = this.source.replace(arg.name, replaceWith)


	# When properly constructing a Method, rely only on the function *this should implement.
	# The class and all other properties are irrelevant. However, they are provided and intended for debugging only.
	def Constructor(this, function, cls):
		this.name = function.__name__
		this.original.cls.object = cls
		if (this.original.cls.object):
			this.original.cls.name = this.original.cls.object.__name__
		this.original.function = function

		this.PopulateFrom(function)
		
		# UpdateSource is called by Functor.PopulateMethods()
		# this.UpdateSource()


	# Grab any known and necessary args from this.kwargs before any Fetch calls are made.
	def PopulatePrecursor(this):
		if (not this.epidef):
			raise MissingArgumentError(f"Call {this.name} from a class instance: {this.original.cls.name}.{this.name}(...). Maybe Functor.PopulateMethods() hasn't been called yet?")

		this.executor = this.epidef.executor

		if ('precursor' in this.kwargs):
			this.precursor = this.kwargs.pop('precursor')
		else:
			this.precursor = None


	# Next is set by Functor.PopulateMethods.
	# We  definitely don't want to Fetch 'next'.
	def PopulateNext(this):
		pass


	# Method.next should be a list of other Methods, as opposed to the standard string; so, instead of Executor.Execute..., we can directly invoke whatever is next.
	# We skip all validation here.
	# We also don't pass any args that were given in the initial function call. Those can all be Fetched from 'precursor'.
	def CallNext(this):
		if (not this.next):
			return None

		for next in this.next:
			next(precursor=this)
