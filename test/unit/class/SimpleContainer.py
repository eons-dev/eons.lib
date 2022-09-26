import sys, os, logging
import eons

class SimpleContainer(eons.DataContainer):
    def __init__(this, name=eons.INVALID_NAME()):
        logging.debug(f"init SimpleContainer")
        super().__init__(name)
