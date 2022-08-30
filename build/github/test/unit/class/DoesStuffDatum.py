import sys, os, logging
import eons as e

class DoesStuffDatum(e.Datum):
    def __init__(this, name=e.INVALID_NAME()):
        logging.info(f"init DoesStuffDatum")
        super().__init__()

        this.extraVariable = "some string"

    def DoStuff(this):
        logging.info(f"{this.name} doing stuff")