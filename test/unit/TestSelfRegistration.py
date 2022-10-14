import pytest
import eons
from Includes import Include, GetIncludePath
Include('datum')

def test_datum_import():
	
	#Before importing class, instantiating a child should fail.
	with pytest.raises(Exception):
		eons.SelfRegistering("DoesStuffDatum")
		assert(False) # just in case something was missed.

	#Load up our child classes.
	eons.SelfRegistering.RegisterAllClassesInDirectory(GetIncludePath('datum'))

	assert(eons.SelfRegistering("DoesStuffDatum") is not None)

