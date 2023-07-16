import eons

@eons.kind(eons.StandardFunctor)
def KindFunctor(
	hello = eons.inject('HelloFunctor'),
	constructor = f"""
this.sayHelloTo = "simplicity!"
""",
):
	this.result.data['kind result'] = hello(this.sayHelloTo)
