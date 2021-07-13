import pytest
import logging
import sys, os
from eons.SelfRegistering import SelfRegistering

def test_datum_import():
    
    #Before importing data, instantiating a child should fail.
    with pytest.raises(Exception):
        SelfRegistering("DoesStuffDatum")
        assert(False) # just in case something was missed.

    #Load up our child classes.
    SelfRegistering.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)),"data"))

    assert(SelfRegistering("DoesStuffDatum") is not None)

