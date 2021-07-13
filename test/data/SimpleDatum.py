import sys, os, logging
from eons import Constants as c
from eons.Datum import Datum

class SimpleDatum(Datum):
    def __init__(self, name=c.INVALID_NAME):
        logging.info(f"init SimpleDatum")
        super().__init__()