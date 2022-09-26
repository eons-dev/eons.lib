import sys, os, logging
import eons

class DoesStuffDatum(eons.Datum):
    def __init__(this, name=eons.INVALID_NAME()):
        logging.info(f"init DoesStuffDatum")
        super().__init__()

        this.extraVariable = "some string"

    def DoStuff(this):
        logging.info(f"{this.name} doing stuff")