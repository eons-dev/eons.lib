import pytest
import logging
import sys, os
import eons

def test_datum_import():
    
    #Before importing class, instantiating a child should fail.
    with pytest.raises(Exception):
        eons.SelfRegistering("DoesStuffDatum")
        assert(False) # just in case something was missed.

    #Load up our child classes.
    eons.SelfRegistering.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "class"))

    assert(eons.SelfRegistering("DoesStuffDatum") is not None)

