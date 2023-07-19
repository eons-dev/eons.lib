import eons

@eons.kind(eons.Functor)
def PartialFunctor(
	words,
	separator,

	hello = eons.inject('HelloFunctor')
):
	return hello(separator.join(words))