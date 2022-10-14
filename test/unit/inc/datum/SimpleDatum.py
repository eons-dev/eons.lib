import logging
import eons

class SimpleDatum(eons.Datum):
	def __init__(this, name=eons.INVALID_NAME()):
		logging.info(f"init SimpleDatum")
		super().__init__()
