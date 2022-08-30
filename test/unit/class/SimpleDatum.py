import sys, os, logging
import eons as e

class SimpleDatum(e.Datum):
    def __init__(this, name=e.INVALID_NAME()):
        logging.info(f"init SimpleDatum")
        super().__init__()