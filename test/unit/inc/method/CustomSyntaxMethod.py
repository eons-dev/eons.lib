import eons
import re

class CustomSyntaxMethod(eons.Method):
	def __init__(this, name="Custom Syntax Method"):
		super().__init__(name)

	def PopulateFrom(this, function):
		super().PopulateFrom(function)

		# Ideally, we allow things like myFunc(++myVal) but this is a simple test, so we only support ^++myVal$, etc.
		this.source = re.sub(r'\+\+(.*)\n', r'\1 = \1 + 1\n', this.source)
