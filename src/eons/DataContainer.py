import logging
import operator
from .Constants import *
from .Datum import Datum

#A DataContainer allows Data to be stored and worked with.
#This class is intended to be derived from and added to.
#Each DataContainer is comprised of multiple Data (see Datum.py for more).
#NOTE: DataContainers are, themselves Data. Thus, you can nest your child classes however you would like.
class DataContainer(Datum):
    def __init__(self, name=INVALID_NAME):
        super().__init__(name)
        self.data = []

    #RETURNS: an empty, invalid Datum.
    def InvalidDatum(self):
        ret = Datum()
        ret.Invalidate()
        return ret

    #Sort things! Requires by be a valid attribute of all Data.
    def SortData(self, by):
        self.data.sort(key=operator.attrgetter(by))

    #Adds a Datum to *this
    def AddDatum(self, datum):
        self.data.append(datum)

    #RETURNS: a Datum with datumAttribute equal to match, an invalid Datum if none found.
    def GetDatumBy(self, datumAttribute, match):
        for d in self.data:
            try: #within for loop 'cause maybe there's an issue with only 1 Datum and the rest are fine.
                if (getattr(d, datumAttribute) == match):
                    return d
            except Exception as e:
                logging.error(f"{self.name} - {e.message}")
                continue
        return self.InvalidDatum()

    #RETURNS: a Datum of the given name, an invalid Datum if none found.
    def GetDatum(self, name):
        return self.GetDatumBy('name', name)

    #Removes all Data in toRem from *this.
    #RETURNS: the Data removed
    def RemoveData(self, toRem):
        self.data = [d for d in self.data if d not in toRem]
        return toRem

    #Removes all Data which match toRem along the given attribute
    def RemoveDataBy(self, datumAttribute, toRem):
        self.data = [d for d in self.data if getattr(d, datumAttribute) not in toRem]
        return toRem

    #Removes all Data in *this except toKeep.
    #RETURNS: the Data removed
    def KeepOnlyData(self, toKeep):
        toRem = [d for d in self.data if d not in toKeep]
        return self.RemoveData(toRem)

    #Removes all Data except those that match toKeep along the given attribute
    #RETURNS: the Data removed
    def KeepOnlyDataBy(self, datumAttribute, toKeep):
        toRem = [d for d in self.data if getattr(d, datumAttribute) not in toKeep]
        return self.RemoveData(toRem)

    #Removes all Data with the name "INVALID NAME"
    #RETURNS: the removed Data
    def RemoveAllUnlabeledData(self):
        toRem = []
        for d in self.data:
            if (d.name =="INVALID NAME"):
                toRem.append(d)
        return self.RemoveData(toRem)

    #Removes all invalid Data
    #RETURNS: the removed Data
    def RemoveAllInvalidData(self):
        toRem = []
        for d in self.data:
            if (not d.IsValid()):
                toRem.append(d)
        return self.RemoveData(toRem)

    #Removes all Data that have an attribute value relative to target.
    #The given relation can be things like operator.le (i.e. <=)
    #   See https://docs.python.org/3/library/operator.html for more info.
    #If ignoreNames is specified, any Data of those names will be ignored.
    #RETURNS: the Data removed
    def RemoveDataRelativeToTarget(self, datumAttribute, relation, target, ignoreNames = []):
        try:
            toRem = []
            for d in self.data:
                if (ignoreNames and d.name in ignoreNames):
                    continue
                if (relation(getattr(d, datumAttribute), target)):
                    toRem.append(d)
            return self.RemoveData(toRem)
        except Exception as e:
            logging.error(f"{self.name} - {e.message}")
            return []

    #Removes any Data that have the same datumAttribute as a previous Datum, keeping only the first.
    #RETURNS: The Data removed
    def RemoveDuplicateDataOf(self, datumAttribute):
        toRem = [] #list of Data
        alreadyProcessed = [] #list of whatever datumAttribute is.
        for d1 in self.data:
            skip = False
            for dp in alreadyProcessed:
                if (getattr(d1, datumAttribute) == dp):
                    skip = True
                    break
            if (skip):
                continue
            for d2 in self.data:
                if (d1 is not d2 and getattr(d1, datumAttribute) == getattr(d2, datumAttribute)):
                    logging.info(f"Removing duplicate Datum {d2} with unique id {getattr(d2, datumAttribute)}")
                    toRem.append(d2)
                    alreadyProcessed.append(getattr(d1, datumAttribute))
        return self.RemoveData(toRem)

    #Adds all Data from otherDataContainer to *this.
    #If there are duplicate Data identified by the attribute preventDuplicatesOf, they are removed.
    #RETURNS: the Data removed, if any.
    def ImportDataFrom(self, otherDataContainer, preventDuplicatesOf=None):
        self.data.extend(otherDataContainer.data);
        if (preventDuplicatesOf is not None):
            return self.RemoveDuplicateDataOf(preventDuplicatesOf)
        return []

