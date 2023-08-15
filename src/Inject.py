from .Functor import Functor
from .SelfRegistering import SelfRegistering
import inspect

# Invoke the External Method machinery to fetch a Functor & return it.
# This should be used with other eons.kinds
class Inject(Functor):
	def __init__(this, name = "Inject"):
		super().__init__(name)
		this.arg.kw.required.append('target')
		this.arg.kw.optional['impl'] = 'External'

		this.arg.mapping.append('target')
		this.arg.mapping.append('impl')

		this.feature.autoReturn = False
	
	def Function(this):
		# Prepare a dummy function to replace with a Method.
		code = compile(f"def {this.target}(this):\n\tpass", '', 'exec')
		exec(code)

		methodToAdd = SelfRegistering(this.impl)
		methodToAdd.Constructor(eval(this.target), None)
		for key, value in this.kwargs.items():
			setattr(methodToAdd, key, value)

		return methodToAdd

def inject(
	target,
	impl="External",
	**kwargs
):
	return Inject()(target=target, impl=impl, **kwargs)
