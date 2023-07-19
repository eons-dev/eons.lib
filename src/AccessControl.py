from .Functor import Functor
from .Inject import inject
from .Utils import util

# AccessControl is used in Kind to control how Surfaces are created on a Functor & what is injected inside them.
# parameters should roughly map to the parameters result of inspect.signature().parameters
class AccessControl(Functor):
	def __init__(this, name = "AccessControl"):
		super().__init__(name)

		this.parameters = util.DotDict()

# Ease of use means of specifying a number of Methods to Inject
class PublicMethods(AccessControl):
	def __init__(this, name = "Public Methods"):
		super().__init__(name)

	def Function(this):
		toInject = {}

		# Functor doesn't allow arbitrary arg handling.
		# for arg in this.parameters:
		# 	toInject[arg] = arg

		for key, value in this.kwargs.items():
			toInject[key] = value
		
		for target, source in toInject.items():
			this.parameters[target] = util.DotDict({
				'kind': None,
				'name': target,
				'default': inject(source)
			})

def public_methods(*args, **kwargs):
	[kwargs.update({arg: arg}) for arg in args]
	return PublicMethods()(**kwargs)