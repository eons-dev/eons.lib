import sys, os, logging
import eons as e

class DoesStuffDatum(e.Datum):
    def __init__(self, name=e.INVALID_NAME()):
        logging.info(f"init DoesStuffDatum")
        super().__init__()

        self.extraVariable = "some string"

    def DoStuff(self):
        logging.info(f"{self.name} doing stuff")