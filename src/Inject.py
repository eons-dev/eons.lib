from .Kind import kind
from .Functor import Functor
from .SelfRegistering import SelfRegistering
import inspect

# Invoke the External Method machinery to fetch a Functor & return it.
# This should be used with other eons.kinds
@kind(Functor)
def Inject(
	target,
	impl="External",
	**kwargs
):
	# Prepare a dummy function to replace with a Method.
	code = compile(f"def {target}(this):\n\tpass", '', 'exec')
	exec(code)

	methodToAdd = SelfRegistering(impl)
	methodToAdd.Constructor(eval(target), None)
	for key, value in kwargs.items():
		setattr(methodToAdd, key, value)

	return methodToAdd

def inject(
	target,
	impl="External",
	**kwargs
):
	return Inject()(target, impl, **kwargs)
