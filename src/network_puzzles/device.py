import copy
from .nic import Nic

class Device:
    #define things by their type for later use in intellisense
    hostname: str
    size: int #a size.  100 or something like that
    uniqueidentifier: str
    location: str #This should be a point, x,y

    def __init__(self, devicerec):
        #define the varables as specific types so intellisense works nicely with it
        self.hostname = devicerec['hostname']
        self.size = int(devicerec['size'])
        self.uniqueidentifier = devicerec['uniqueidentifier']
        self.location = devicerec['location']
        self.mtype = devicerec['mytype']
        self.isdns = devicerec['isdns']
        self.isdhcp = devicerec['isdhcp']
        self.nic = []
        if not isinstance(devicerec['nic'], list):
            devicerec['nic'] = [ devicerec['nic'] ] #turn it into a list if it was not one before
        for onenic in devicerec['nic']:
            #loop through them and add them separately
            tnic = Nic(onenic)
            self.nic.append(tnic)