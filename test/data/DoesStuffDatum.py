import sys, os, logging
from eons import Constants as c
from eons.Datum import Datum

class DoesStuffDatum(Datum):
    def __init__(self, name=c.INVALID_NAME):
        logging.info(f"init DoesStuffDatum")
        super().__init__()

        self.extraVariable = "some string"

    def DoStuff(self):
        logging.info(f"{self.name} doing stuff")