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
	def ParseParameters(functor, args, source, ctor, strongType = False):
		# Code duplicated from Method.PopulateFrom. See that class for more info.
		for arg in args.values():
			if (arg.name == 'constructor' or arg.name == '__init__'):
				if (hasattr(arg, 'type') and "eons.eons" in str(arg.type)):
					ctor.additions += f"""
this.constructor = {str(arg.type)[8:-2]}()
this.constructor.epidef = this
this.constructor()
"""
				else:
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
							ctor,
							strongType=strongType
						)
						shouldMapArg = False
					else:
						defaultValue = arg.default
						if (isinstance(arg.default, str)):
							defaultValue = f"'{arg.default}'"
						ctor.source.append(f"this.arg.kw.optional['{arg.name}'] = {defaultValue}")
				else:
					ctor.source.append(f"this.arg.kw.required.append('{arg.name}')")

				if (strongType and hasattr(arg, 'type')):
					ctor.source.append(f"""
	try:
		this.arg.type['{arg.name}'] = {arg.type.__name__}
	except:
		this.arg.type['{arg.name}'] = eons.SelfRegistering('{arg.type.__name__}')
""")

				if (shouldMapArg):
					ctor.source.append(f"this.arg.mapping.append('{arg.name}')")

			# Source mangling
			# TODO: Expand as we have more solid test cases.
			source = re.sub(fr"{arg.name}([\s\[\]\.\(\)\}}\*\+/-=%,]|$)", fr"{replaceWith}\1", source)
			
		return functor, source, ctor

	# Python requires us to manually build the meta class when resolving diamod inheritance.
	def GetCommonMetaClass(bases):
		# Collect metaclasses from bases
		metaclasses = [type(base) for base in bases]
		if len(metaclasses) == 1:
			return metaclasses[0]

		# Ensure all metaclasses are compatible
		commonMeta = metaclasses[0]
		for meta in metaclasses[1:]:
			if not issubclass(meta, commonMeta):
				# Merge metaclasses if they are not compatible
				class MergedMeta(meta, commonMeta):
					pass
				commonMeta = MergedMeta
		return commonMeta


	def FunctionToFunctor(function, functorName=None, args=None, source=None, strongType=False):
		executor = ExecutorTracker.GetLatest()
		shouldLog = executor and executor.verbosity > 3
		
		destinedModule = inspect.getmodule(function)
		destinedModuleName = INVALID_NAME()
		if (destinedModule):
			destinedModuleName = destinedModule.__name__
		pivotModule = None
		if (not destinedModule):
			pivotModule = inspect.currentframe().f_back
			if (not str(pivotModule).endswith('<module>>')):
				pivotModule = None

		bases = base
		if (isinstance(bases, type)):
			bases = [bases]

		try:
			primaryFunctionName = bases[0].primaryFunctionName
		except Exception as e:
			# Just add some logs, but don't try to fix.
			# This is fatal (i.e. something larger is wrong than just the name 'Function' missing).
			logging.error(f"Failed to get primary function name from {bases[0]}: {e}")
			logging.debug(f"bases: {bases}")
			raise e

		# Ensure all bases are classes
		bases = [type(base) if not isinstance(base, type) else base for base in bases]

		if (functorName is None):
			functorName = function.__name__

		logging.debug(f"Creating '{functorName}' from {bases} in module '{destinedModuleName if destinedModule else 'eons'}'")

		functor = GetCommonMetaClass(bases)(
			functorName,
			(*bases,),
			{}
		)

		if ('name' not in kwargs):
			kwargs['name'] = functorName

		if (args is None):
			args = inspect.signature(function).parameters
		if (source is None):
			source = inspect.getsource(function)

		source = source[source.find(':\n')+1:].strip() # Will fail if an arg has ':\n' in it
		source = re.sub(r'(^|[\s\[\(\{\*\+/-=%\^,])epidef([\s\[\]\.\(\)\}\*\+/-=%\^,]|$)', r'\1this.epidef\2', source)

		ctor = util.DotDict()
		ctor.source = []
		ctor.additions = ""

		functor, source, ctor = ParseParameters(functor, args, source, ctor, strongType=strongType)

		# Constructor creation
		constructorName = f"_eons_constructor_{kwargs['name']}"
		constructorSource = f"def {constructorName}(this, name='{functorName}', **kwargs):"
		constructorSource += "\n\timport sys"
		constructorSource += "\n\timport eons"
		constructorSource += f'''
	this.name = name # For debugging
	try:
		{functor.__name__} = importedAs = eons.util.BlackMagick.GetCurrentFunction().__source_class__
		if (not isinstance(this, {functor.__name__})):
			raise Exception('{functor.__name__} not in source class')
	except Exception as e1:
		try:
			importedAs = eons.util.BlackMagick.GetCurrentFunction().__pivot_module__.f_locals['__imported_as__']
			{functor.__name__} = sys.modules[importedAs].{functor.__name__}
			if (not isinstance(this, {functor.__name__})):
				raise Exception('{functor.__name__} not in {{importedAs}}')
		except Exception as e2:
			try:
				{functor.__name__} = sys.modules[{destinedModuleName}].{functor.__name__}
				if (not isinstance(this, {functor.__name__})):
					raise Exception('{functor.__name__} not in {destinedModuleName}')
			except Exception as e3:
				logging.warning(f"Failed to initialize {functor.__name__}: \\n{{e1}}\\n{{e2}}\\n{{e3}}")
				# Catch all. This will cause an infinite loop if this != {functor.__name__}
				{functor.__name__} = this.__class__
	this.parent = type(this).mro()[1]
	super({functor.__name__}, this).__init__(**kwargs)
	this.name = name # For use
'''
		constructorSource += '\n\t' + '\n\t'.join(ctor.source)
		if (len(ctor.additions)):
			re.sub(r'^\s+', '\n', ctor.additions)
			constructorSource += '\n\t' + ('\n\t'.join(ctor.additions.split('\n'))).replace('self', 'this')
		if (shouldLog):
			logging.debug(f"Constructor source for {kwargs['name']}:\n{constructorSource}")
		code = compile(constructorSource, '', 'exec')
		exec(code)
		exec(f'functor.__init__ = {constructorName}')
		functor.__init__.__source_class__ = functor
		functor.__init__.__pivot_module__ = pivotModule

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

		if (not destinedModule):
			destinedModuleName = 'eons.eons'

		try:
			setattr(sys.modules[destinedModuleName], functorName, functor)
		except Exception as e:
			logging.warning(f"Failed to set {functorName} in {destinedModuleName}: {e}")

		return functor

	return FunctionToFunctor
