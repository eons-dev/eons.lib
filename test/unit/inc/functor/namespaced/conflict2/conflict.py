import eons

@eons.namespace('conflict2')
@eons.kind(eons.Functor)
def conflict(
	num = 2
):
	return num