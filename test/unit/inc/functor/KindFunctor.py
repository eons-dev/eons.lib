import eons

@eons.kind(eons.StandardFunctor)
def KindFunctor(
	methods = eons.public_methods(hello = 'HelloFunctor'),
	constructor = f"""
this.sayHelloTo = "simplicity!"
""",
):
	this.result.data['kind result'] = hello(this.sayHelloTo)
