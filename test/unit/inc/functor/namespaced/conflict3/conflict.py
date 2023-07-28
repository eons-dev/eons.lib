import eons

@eons.namespace('conflict3')
@eons.kind(eons.Functor)
def conflict(
	num = 3
):
	return num