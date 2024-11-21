import eons
import sys
import logging

# Try resolving a ModuleNotFoundError by installing the module through our repo.
class observe(eons.ErrorResolution):
	def __init__(this, name="observe"):
		super().__init__(name)

		this.ApplyTo('ModuleNotFoundError', "No module named 'SUBJECT'")

	def Resolve(this):
		this.executor.Observe(this.error.subject)
		# The regionOfInterest (i.e. the error.subject here) is mangled through Observation.
		# TODO: Can we ge the executor to report the new module name or otherwise check for a successful Observation?
		this.error.resolution.successful = True
