import sys, os, logging
from eons import Constants as c
from eons.DataContainer import DataContainer

class SimpleContainer(DataContainer):
    def __init__(self, name=c.INVALID_NAME):
        logging.debug(f"init SimpleContainer")
        super().__init__(name)
