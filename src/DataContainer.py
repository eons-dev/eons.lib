import logging
import operator
from .Constants import *
from .Datum import Datum

# A DataContainer allows Data to be stored and worked with.
# This class is intended to be derived from and added to.
# Each DataContainer is comprised of multiple Data (see Datum.py for more).
# NOTE: DataContainers are, themselves Data. Thus, you can nest your child classes however you would like.
class DataContainer(Datum):
    def __init__(this, name=INVALID_NAME()):
        super().__init__(name)
        this.data = []

    # RETURNS: an empty, invalid Datum.
    def InvalidDatum(this):
        ret = Datum()
        ret.Invalidate()
        return ret

    # Sort things! Requires by be a valid attribute of all Data.
    def SortData(this, by):
        this.data.sort(key=operator.attrgetter(by))

    # Adds a Datum to *this
    def AddDatum(this, datum):
        this.data.append(datum)

    # RETURNS: a Datum with datumAttribute equal to match, an invalid Datum if none found.
    def GetDatumBy(this, datumAttribute, match):
        for d in this.data:
            try: # within for loop 'cause maybe there's an issue with only 1 Datum and the rest are fine.
                if (str(getattr(d, datumAttribute)) == str(match)):
                    return d
            except Exception as e:
                logging.error(f"{this.name} - {e.message}")
                continue
        return this.InvalidDatum()

    # RETURNS: a Datum of the given name, an invalid Datum if none found.
    def GetDatum(this, name):
        return this.GetDatumBy('name', name)

    # Removes all Data in toRem from *this.
    # RETURNS: the Data removed
    def RemoveData(this, toRem):
        # logging.debug(f"Removing {toRem}")
        this.data = [d for d in this.data if d not in toRem]
        return toRem

    # Removes all Data which match toRem along the given attribute
    def RemoveDataBy(this, datumAttribute, toRem):
        toRem = [d for d in this.data if str(getattr(d, datumAttribute)) in list(map(str, toRem))]
        return this.RemoveData(toRem)

    # Removes all Data in *this except toKeep.
    # RETURNS: the Data removed
    def KeepOnlyData(this, toKeep):
        toRem = [d for d in this.data if d not in toKeep]
        return this.RemoveData(toRem)

    # Removes all Data except those that match toKeep along the given attribute
    # RETURNS: the Data removed
    def KeepOnlyDataBy(this, datumAttribute, toKeep):
        # logging.debug(f"Keeping only class with a {datumAttribute} of {toKeep}")
        # toRem = []
        # for d in this.class:
        #     shouldRem = False
        #     for k in toKeep:
        #         if (str(getattr(d, datumAttribute)) == str(k)):
        #             logging.debug(f"found {k} in {d.__dict__}")
        #             shouldRem = True
        #             break
        #     if (shouldRem):
        #         toRem.append(d)
        #     else:
        #         logging.debug(f"{k} not found in {d.__dict__}")
        toRem = [d for d in this.data if str(getattr(d, datumAttribute)) not in list(map(str, toKeep))]
        return this.RemoveData(toRem)

    # Removes all Data with the name "INVALID NAME"
    # RETURNS: the removed Data
    def RemoveAllUnlabeledData(this):
        toRem = []
        for d in this.data:
            if (d.name =="INVALID NAME"):
                toRem.append(d)
        return this.RemoveData(toRem)

    # Removes all invalid Data
    # RETURNS: the removed Data
    def RemoveAllInvalidData(this):
        toRem = []
        for d in this.data:
            if (not d.IsValid()):
                toRem.append(d)
        return this.RemoveData(toRem)

    # Removes all Data that have an attribute value relative to target.
    # The given relation can be things like operator.le (i.e. <=)
    #   See https://docs.python.org/3/library/operator.html for more info.
    # If ignoreNames is specified, any Data of those names will be ignored.
    # RETURNS: the Data removed
    def RemoveDataRelativeToTarget(this, datumAttribute, relation, target, ignoreNames = []):
        try:
            toRem = []
            for d in this.data:
                if (ignoreNames and d.name in ignoreNames):
                    continue
                if (relation(getattr(d, datumAttribute), target)):
                    toRem.append(d)
            return this.RemoveData(toRem)
        except Exception as e:
            logging.error(f"{this.name} - {e.message}")
            return []

    # Removes any Data that have the same datumAttribute as a previous Datum, keeping only the first.
    # RETURNS: The Data removed
    def RemoveDuplicateDataOf(this, datumAttribute):
        toRem = [] # list of Data
        alreadyProcessed = [] # list of strings, not whatever datumAttribute is.
        for d1 in this.data:
            skip = False
            for dp in alreadyProcessed:
                if (str(getattr(d1, datumAttribute)) == dp):
                    skip = True
                    break
            if (skip):
                continue
            for d2 in this.data:
                if (d1 is not d2 and str(getattr(d1, datumAttribute)) == str(getattr(d2, datumAttribute))):
                    logging.info(f"Removing duplicate Datum {d2} with unique id {getattr(d2, datumAttribute)}")
                    toRem.append(d2)
                    alreadyProcessed.append(str(getattr(d1, datumAttribute)))
        return this.RemoveData(toRem)

    # Adds all Data from otherDataContainer to *this.
    # If there are duplicate Data identified by the attribute preventDuplicatesOf, they are removed.
    # RETURNS: the Data removed, if any.
    def ImportDataFrom(this, otherDataContainer, preventDuplicatesOf=None):
        this.data.extend(otherDataContainer.data);
        if (preventDuplicatesOf is not None):
            return this.RemoveDuplicateDataOf(preventDuplicatesOf)
        return []

