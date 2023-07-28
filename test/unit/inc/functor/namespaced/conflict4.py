import eons

@eons.kind(eons.Functor)
def conflict4(
	public = eons.public_methods(
		'conflict'
	)
):
	return conflict()