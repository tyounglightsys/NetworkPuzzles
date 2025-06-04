#!/usr/bin/python3
#All the functions needed for reading the EduNetwork Puzzle file
#And getting information from it
import json
import copy
import re
import os

# define the global network list
from . import session
from . import packet
from . import device
from .nic import Nic


class Puzzle:
    """Encapsulates the loaded puzzle's data and functionality."""
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError(f"Invalid JSON data passed to {self.__class__}.")
        self.json = data

    def all_devices(self):
        """
        Return a list that contains all devices in the puzzle.
        """
        devices = []
        for one in self.json.get('device', []):
            if 'hostname' in one:
                devices.append(one)
        return devices

    def all_links(self):
        """
        Return a list that contains all links in the puzzle.
        """
        links = []
        for one in self.json.get('link', []):
            if 'hostname' in one:
                links.append(one)
        return links

    def arp_lookup(self, ipaddr):
        return device.globalArpLookup(ipaddr)

    def device_from_name(self, name):
        return self._item_by_attrib(self.all_devices(), 'hostname', name)

    def device_from_uid(self, uid):
        uid = str(uid)  # ensure not an integer
        return self._item_by_attrib(self.all_devices(), 'uniqueidentifier', uid)

    def item_from_uid(self, uid):
        """Return the item matching the ID.  Could be a device, a link, or a nic"""
        result = self.device_from_uid(uid)
        if result is not None:
            return result
        result = self.link_from_uid(uid)
        if result is not None:
            return result
        result = self.nic_from_uid(uid)
        if result is not None:
            return result
        return None

    def link_from_devices(self, srcDevice, dstDevice):
        """return a link given the two devices at either end
        Args:
            srcDevice:Device - the device itself
            srcDevice:str - the hostname of the device
            dstDevice:device - the device itself
            dstDevice:str - the hostname of the device
        Returns: a link record or None
        """
        srcstr=""
        dststr=""
        if isinstance(srcDevice, str):
            srcstr = srcDevice
        else:
            if 'hostname' in srcDevice:
                srcstr = srcDevice.get('hostname')
        if isinstance(dstDevice, str):
            dststr = dstDevice
        else:
            if 'hostname' in dstDevice:
                dststr = dstDevice.get('hostname')
        # Now we should have srcstr and dststr set.  Use them to concoct a link name
        # The link name looks like: pc0_link_pc1
        result = session.puzzle.link_from_name(srcstr + "_link_" + dststr)
        if result is not None:
            return result
        result = session.puzzle.link_from_name(dststr + "_link_" + srcstr)
        if result is not None:
            return result
        # if we get here, we could not find it. Return none
        return None

    def link_from_name(self, name):
        return self._item_by_attrib(self.all_links(), 'hostname', name)

    def link_from_uid(self, uid):
        return self._item_by_attrib(self.all_links(), 'uniqueidentifier', uid)

    def nic_from_uid(self, uid):
        """find the network card from the id
        Args: uid: int - the device id for the nic you are looking for
        Notes:
            Each component on the network has a unique ID.  PCs can change names, so we do not assume host-names are unique.
            Thus, for a network link (ethernet cable, wireless, etc) to know what two devices it is connecting, we use the ID
        """
        for d in self.all_devices():
            item = self._item_by_attrib(d.get('nic'), 'uniqueidentifier', uid)
            if item:
                return item
        return None

    def set_all_device_nic_macs(self):
        for oneDevice in self.all_devices():
            if not isinstance(oneDevice['nic'], list):
                oneDevice['nic'] = [oneDevice['nic']]
            for oneNic in oneDevice['nic']:
                oneNic = Nic(oneNic).ensure_mac()

    def _item_by_attrib(self, items: list, attrib: str, value: str) -> dict|None:
        # Returns first match; i.e. assumes only one item in list matches given
        # attribute. It also assumes that 'items' is a list of dicts or json data.
        for item in items:
            if item.get(attrib) == value:
                return item


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
            oneentry = read_json_file(file_path)
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
        session.puzzle = Puzzle(puz)
        session.puzzle.set_all_device_nic_macs()
    return puz

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
    print(mynet['name'])
    mydevice = session.puzzle.device_from_uid('110')
    #print(mydevice)
    #mynic=device.nicFromName(mydevice,'eth0')
    mynic = session.puzzle.nic_from_uid('112')
    #print(mynic)
    mylink = session.puzzle.link_from_uid('121')
    print(mylink)
