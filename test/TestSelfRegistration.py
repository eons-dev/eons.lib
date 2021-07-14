import pytest
import logging
import sys, os
import eons as e

def test_datum_import():
    
    #Before importing data, instantiating a child should fail.
    with pytest.raises(Exception):
        e.SelfRegistering("DoesStuffDatum")
        assert(False) # just in case something was missed.

    #Load up our child classes.
    e.SelfRegistering.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)),"data"))

    assert(e.SelfRegistering("DoesStuffDatum") is not None)

