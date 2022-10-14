import logging
import eons
from Includes import Include

Include('datum')

from SimpleDatum import SimpleDatum

def test_datum_creation_via_this_registering():
	logging.info("Creating SimpleDatum via this Registration")
	# datum = SelfRegistering("SimpleDatum", name="R4ND0M N4M3") #TODO: How do?
	datum = eons.SelfRegistering("SimpleDatum")
	logging.info(f"datum = {datum.__dict__}")
	# logging.info("Done")
	assert(datum is not None)
	
def test_datum_creation_via_direct_init():
	logging.info("Creating SimpleDatum via direct initialization")
	datum = SimpleDatum("SimpleDatum")
	logging.info(f"datum = {datum.__dict__}")
	# logging.info("Done")
	assert(datum is not None)
