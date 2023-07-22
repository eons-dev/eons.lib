import eons

@eons.namespace('conflict1')
@eons.kind(eons.Functor)
def conflict(
	num = 1
):
	return num
