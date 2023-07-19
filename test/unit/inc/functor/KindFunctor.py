import eons

@eons.kind(eons.Functor)
def KindChild():
	return caller.sayHelloTo

@eons.kind(eons.StandardFunctor)
def KindFunctor(
	methods = eons.public_methods(
		'KindChild',
    	hello = 'HelloFunctor'
	),
	constructor = f"""
this.sayHelloTo = "simplicity!"
""",
):
	this.result.data['kind_result'] = hello(KindChild().returned)
