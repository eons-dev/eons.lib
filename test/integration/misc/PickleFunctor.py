import eons
import dill as pickle

@eons.kind(eons.Functor)
def PickleMe(
	testval = "it works!"
):
	print(testval)

with pickle.detect.trace():
	pickle.loads(pickle.dumps(PickleMe))()()