import pytest
import logging
import sys, os
import eons as e

sys.path.append(os.path.join((os.path.dirname(os.path.abspath(__file__))), "data"))

from SimpleDatum import SimpleDatum

def test_datum_creation_via_self_registering():
    logging.info("Creating SimpleDatum via self Registration")
    # datum = SelfRegistering("SimpleDatum", name="R4ND0M N4M3") #TODO: How do?
    datum = e.SelfRegistering("SimpleDatum")
    logging.info(f"datum = {datum.__dict__}")
    # logging.info("Done")
    assert(datum is not None)
    
def test_datum_creation_via_direct_init():
    logging.info("Creating SimpleDatum via direct initialization")
    datum = SimpleDatum("SimpleDatum")
    logging.info(f"datum = {datum.__dict__}")
    # logging.info("Done")
    assert(datum is not None)
