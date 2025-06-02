#!/usr/bin/python3
#All the functions needed for reading the EduNetwork Puzzle file
#And getting information from it
import json
import copy
import re
import os
import time

# define the global network list
from . import session
from . import packet
from . import device


class Puzzle:
    def __init__(self, data):
        self.data = data
        self._devices = []
        self._links = []
        self._mac_list = []

    def arp_lookup(self, ipaddr):
        return device.globalArpLookup(ipaddr)

    def device_from_name(self, name):
        # return self._item_by_attrib(self.devices, 'hostname', name)
        return self._item_by_prop(self.devices, 'hostname', name)

    def device_from_uid(self, uid):
        return self._item_by_attrib(self.devices, 'uniqueidentifier', uid)

    def link_from_name(self, name):
        return self._item_by_attrib(self.links, 'hostname', name)

    def link_from_uid(self, uid):
        return self._item_by_attrib(self.links, 'uniqueidentifier', uid)

    def _item_by_attrib(self, items: list, attrib: str, value: str) -> dict|None:
        # Returns first match; i.e. assumes only one item in list matches given
        # attribute. It also assumes that 'items' is a list of dicts or json data.
        for item in items:
            if item.get(attrib) == value:
                return item

    def _item_by_prop(self, items, prop, value):
        # Returns first match; i.e. assumes only one item in list matches given
        # attribute.
        for item in items:
            if not hasattr(item, prop):
                raise AttributeError
            if item.__dict__.get(prop) == value:
                return item

    @property
    def devices(self):
        """A list of all the devices in the puzzle."""
        return self._devices
    
    @devices.setter
    def devices(self):
        self._devices = device.allDevices()

    @property
    def links(self):
        """A list of all the links in the puzzle."""
        return self._links

    @links.setter
    def links(self):
        self._links = device.allLinks()

    @property
    def mac_list(self):
        """A list of all the MACs in the puzzle."""
        return self._mac_list

    @mac_list.setter
    def mac_list(self):
        """Build/rebuild the global MAC list.  Should be run when we load a new puzzle, when we change IPs, or add/remove NICs."""
        macs = []
        # session.maclist = [] #clear it out
        for onedevice in self.devices:
            #print ("finding macs for " + onedevice['hostname'])
            for onemac in device.maclistFromDevice(onedevice):
                macs.append(onemac)
        self._macs = macs
        session.maclist = macs


def read_json_file(file_path):
    """
    Reads a JSON file and returns the data as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The JSON data as a Python dictionary, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {file_path}")
        return None

def matches_filter(name: str, pattern: str|None) -> bool:
    if pattern is None:
        return True
    elif re.match(pattern, name, re.IGNORECASE):
        return True
    else:
        return False

def filter_items(items: list, pattern: str, json_files: bool = False) -> list:
    filtered_items = []
    for item in items:
        if not json_files:
            name = item['EduNetworkBuilder']['Network']['name']
        else:
            name = re.sub(r"\.json","", item)
        if matches_filter(name, pattern):
            filtered_items.append(name)
    return filtered_items

def listPuzzlesFromDisk(regex_pattern: str = None):
    directory_path="src/network_puzzles/resources/puzzles"
    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    return filter_items(files, regex_pattern, json_files=True)

def listPuzzles(regex_pattern: str = None):
    if len(session.puzzlelist) == 0:
        readPuzzle()
    return filter_items(session.puzzlelist, regex_pattern)

def readPuzzle():
    """Read in the puzzles from the various .json files"""
    if len(session.puzzlelist) == 0:
        allfiles=listPuzzlesFromDisk("Level.*")
        for one in allfiles:
            #We stripped off the ".json" from the name, so we need to add it back
            file_path = 'src/network_puzzles/resources/puzzles/' + one + ".json"
            oneentry =read_json_file(file_path)
            oneentry['EduNetworkBuilder']['Network']['name'] = one
            session.puzzlelist.append(oneentry)
            #print("loading: " + one)
        session.puzzlelist.sort(key = lambda x: (float(x['EduNetworkBuilder']['Network']['level']), float(x['EduNetworkBuilder']['Network']['sortorder']) ))

def choosePuzzleFromName(what:str):
    """
    Choose a puzzle using the puzzle name.
    Args: 
        what: string - The puzzle name, matching case and everything, of the puzzle we want to select
    """
    readPuzzle()
    #print ("Length of puzzleslist: " + str(len(puzzlelist)))

    for one in session.puzzlelist:
        if one['EduNetworkBuilder']['Network']['name'] == what:
            return copy.deepcopy(one['EduNetworkBuilder']['Network'])

def choosePuzzle(what, filter=None):
    """
    Choose a puzzle from the list of available puzzles.
    Args: 
        what: int - the index of the puzzle we want to select
        what: str - use choosePuzzleFromName
        filter: str - this is a filter to use.  For example ".*DHCP.*".  Then the int would apply to the index in the filtered list
    """
    readPuzzle()
    if filter is not None:
        #We have a filter.  We need to try to look up the item from the filtered list
        filteredList=listPuzzles(filter)
        if len(filteredList) > 0:
            #this means it is a valid filter. Try to use it.
            try:
                what = filteredList[int(what)]
            except Exception:
                #It did not work.  Ignore the filter.
                1 #This command does nothing.  It allows us to have an exception that does not blow anything up

    if isinstance(what,int):
       puz = copy.deepcopy(session.puzzlelist[what]['EduNetworkBuilder']['Network'])
    else:
        try:
            #if the int(what) fails, we treat it as a name
            puz = copy.deepcopy(session.puzzlelist[int(what)]['EduNetworkBuilder']['Network'])
        except Exception:
            puz = choosePuzzleFromName(what)
    if puz is not None:
        print("Loaded: " + puz['name'])
        session.puzzle = puz
        setAllDeviceNICMacs()
    return puz

def setAllDeviceNICMacs():
    for oneDevice in device.allDevices():
        if not isinstance(oneDevice['nic'], list):
            oneDevice['nic'] = [oneDevice['nic']]
        for oneNic in oneDevice['nic']:
            device.AssignMacIfNeeded(oneNic)

def justIP(ip):
    """return just the IP address as a string, stripping the subnet if there was one"""
    return packet.justIP(ip)

def is_ipv4(string):
        """
        return True if the string is a valid IPv4 address.
        """
        return packet.is_ipv4(string)

def doTest():

    #mynet=choosePuzzlek('Level0-NeedsLink')
    mynet=choosePuzzle(3)
    print (mynet['name'])
    mydevice=device.deviceFromID('110')
    #print(mydevice)
    #mynic=device.nicFromName(mydevice,'eth0')
    mynic=device.nicFromID('112')
    #print(mynic)
    mylink=device.linkFromID('121')
    print(mylink)
