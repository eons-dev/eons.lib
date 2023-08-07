from .Functor import Functor
from .StandardFunctor import StandardFunctor
from .Constants import *
from .SelfRegistering import SelfRegistering
from .ExecutorTracker import ExecutorTracker
from .Method import Method, PrepareClassMethod
from .AccessControl import AccessControl
from .Utils import util
import inspect
import logging
import re

def kind(
	base = StandardFunctor,
	**kwargs
):
	def ParseParameters(functor, args, source, ctor):
		# Code duplicated from Method.PopulateFrom. See that class for more info.
		for arg in args.values():
			if (arg.name == 'constructor' or arg.name == '__init__'):
				ctor.additions += f"{arg.default}\n"
				continue

			replaceWith = arg.name

			# *args
			if (arg.kind == inspect.Parameter.VAR_POSITIONAL):
				replaceWith = 'this.args'

			# **kwargs
			elif (arg.kind == inspect.Parameter.VAR_KEYWORD):
				replaceWith = 'this.kwargs'

			# Normal argument
			else:
				replaceWith = f'this.{arg.name}'
				shouldMapArg = arg.kind in [inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY]

				if (arg.default != inspect.Parameter.empty):
					if (isinstance(arg.default, Method)):
						arg.default.name = arg.name # Rename the Functor to match what was requested
						PrepareClassMethod(functor, arg.name, arg.default)
						shouldMapArg = False
					elif (isinstance(arg.default, AccessControl)):
						# NOTE: arg.name is discarded.
						functor, source, ctor = ParseParameters(
							functor,
							arg.default.parameters,
							source,
							ctor
						)
						shouldMapArg = False
					else:
						defaultValue = arg.default
						if (isinstance(arg.default, str)):
							defaultValue = f"'{arg.default}'"
						ctor.source.append(f"this.optionalKWArgs['{arg.name}'] = {defaultValue}")
				else:
					ctor.source.append(f"this.requiredKWArgs.append('{arg.name}')")

				if (shouldMapArg):
					ctor.source.append(f"this.argMapping.append('{arg.name}')")

			# Source mangling
			# TODO: Expand as we have more solid test cases.
			source = re.sub(fr"{arg.name}([\s\[\]\.\(\)\}}\*\+/-=%,]|$)", fr"{replaceWith}\1", source)
			
		return functor, source, ctor

	def FunctionToFunctor(function):
		executor = ExecutorTracker.GetLatest()
		shouldLog = executor and executor.verbosity > 3

		bases = base
		if (isinstance(bases, type)):
			bases = [bases]
		
		primaryFunctionName = bases[0].primaryFunctionName

		functor = type(
			function.__name__,
			(*bases,),
			{}
		)

		if ('name' not in kwargs):
			kwargs['name'] = function.__name__
	
		args = inspect.signature(function).parameters
		source = inspect.getsource(function)
		source = source[source.find(':\n')+1:].strip() # Will fail if an arg has ':\n' in it
		source = re.sub(r'caller([\s\[\]\.\(\)\}\*\+/-=%,]|$)', r'this.caller\1', source)

		ctor = util.DotDict()
		ctor.source = []
		ctor.additions = ""

		functor, source, ctor = ParseParameters(functor, args, source, ctor)

		# Constructor creation
		constructorName = f"_eons_constructor_{kwargs['name']}"
		constructorSource = f"def {constructorName}(this, name='{function.__name__}'):"
		ctor.source.insert(0, f"super(this.__class__, this).__init__(name)")
		constructorSource += '\n\t' + '\n\t'.join(ctor.source)
		if (len(ctor.additions)):
			re.sub(r'^\s+', '\n', ctor.additions)
			constructorSource += '\n\t' + ('\n\t'.join(ctor.additions.split('\n'))).replace('self', 'this')
		if (shouldLog):
			logging.debug(f"Constructor source for {kwargs['name']}:\n{constructorSource}")
		code = compile(constructorSource, '', 'exec')
		exec(code)
		exec(f'functor.__init__ = {constructorName}')

		wrappedPrimaryFunction = f"_eons_method_{kwargs['name']}"
		completeSource = f'''\
def {wrappedPrimaryFunction}(this):
	{source}
'''
		if (shouldLog):
			logging.debug(f"Primary function source for {kwargs['name']}:\n{completeSource}")
		code = compile(completeSource, '', 'exec')
		exec(code)
		exec(f'functor.{primaryFunctionName} = {wrappedPrimaryFunction}')

		return functor

	return FunctionToFunctor
