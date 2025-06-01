#!/usr/bin/python3
#All the functions needed for reading the EduNetwork Puzzle file
#And getting information from it
import ipaddress
import json
import copy
import random
import re
import os
import time

# define the global network list
from . import session
from . import packet
from . import device
from . import nic

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
    for oneDevice in allDevices():
        if not isinstance(oneDevice['nic'], list):
            oneDevice['nic'] = [oneDevice['nic']]
        for oneNic in oneDevice['nic']:
            device.AssignMacIfNeeded(oneNic)

def allDevices():
    """
    Return a list that contains all devices in the puzzle.
    """
    return device.allDevices()

def allLinks():
    """
    Return a list that contains all devices in the puzzle.
    """
    return device.allLinks()


def maclistFromDevice(src):
    """
    Return a list of all the MAC addresses of all the nics on the device
    Args:
        src:str - lookup the source device using the hostname and return all MAC addresses
        src:device - lookup all the MAC addresses in this device

    Returns:
        A list of mac-addresses.  Each MAC is a struct containing at least the ip and mac.
    """
    return device.maclistFromDevice(src)


def buildGlobalMACList():
    """Build/rebuild the global MAC list.  Should be run when we load a new puzzle, when we change IPs, or add/remove NICs."""
    # global maclist
    device.buildGlobalMACList()

def justIP(ip):
    """return just the IP address as a string, stripping the subnet if there was one"""
    return packet.justIP(ip)


def globalArpLookup(ip):
    """Look up an IP address in the global ARP database.
    Args:
        ip:str the IP address as a string.
        ip:ipaddress the IP as an ipaddress
    Returns:
        The MAC address corresponding to the IP as a string or None.
    """
    return device.globalArpLookup(ip)

def arpLookup(srcDevice, ip):
    """find a mac address, with the source being the specified device
    Args:
        srcDevice:str the hostname of the device we are looking at
        srcDevice:device the device record we are looking at
        ip:str the string ip address we are trying to find
        ip:ipaddress the ip address we are trying to find
        """
    return device.arpLookup(srcDevice, ip)


def get_item_by_attrib(items: list, attrib: str, value: str) -> dict|None:
    # Returns first match; i.e. assumes only one item in list matches given
    # attribute.
    for item in items:
        if item.get(attrib) == value:
            return item

def nicFromName(theDevice,what):
    """return the network card from the name
    Args:
        theDevice:str - the hostname of the device that contains the nic we are looking for
        theDevice:device - the device containing the nic we are looking for
        what:str - the network card name we are looking for
    Returns:
        the network card record from the device or None
        """
    # if isinstance(theDevice, str):
    #     theDevice = deviceFromName(theDevice)
    # if theDevice is None:
    #     return None
    # return get_item_by_attrib(theDevice.get('nic'), 'nicname', what)
    return device.nicFromName(theDevice,what)

def nicFromID(what):
    """find the network card from the id
    Args: what:int - the device id for the nic you are looking for
    Notes:
        Each component on the network has a unique ID.  PCs can change names, so we do not assume host-names are unique.
        Thus, for a network link (ethernet cable, wireless, etc) to know what two devices it is connecting, we use the ID
    """
    # for theDevice in allDevices():
    #     item = get_item_by_attrib(theDevice.get('nic'), 'uniqueidentifier', what)
    #     if item:
    #         return item
    # return None
    return nicFromID(what)

def deviceFromName(what: str) -> dict|None:
    """Return the device, given a name
    Args: what:str the hostname of the device
    returns the device matching the name, or None"""
    # return get_item_by_attrib(allDevices(), 'hostname', what)
    return device.deviceFromName(what)

def deviceFromID(what: str) -> dict|None:
    """Return the device, given a name
    Args: what:int the unique id of the device
    returns the device matching the id, or None"""
    # return get_item_by_attrib(allDevices(), 'uniqueidentifier', what)
    return device.deviceFromID(what)

def linkFromName(what:str) -> dict|None:
    """
    Return the link matching the name
    Args: what:str - the string name of the link
    returns: the link record or None
    """
    # return get_item_by_attrib(allLinks(), 'hostname', what)
    return device.linkFromName(what)

def linkFromDevices(srcDevice, dstDevice):
    """return a link given the two devices at either end
    Args:
        srcDevice:Device - the device itself
        srcDevice:str - the hostname of the device
        dstDevice:device - the device itself
        dstDevice:str - the hostname of the device
    Returns: a link record or None
    """
    return device.linkFromDevices(srcDevice,dstDevice)

def linkFromID(what):
    """
    Return the link matching the id
    Args: what:int - the unique id of the link
    Returns: the matching link record or None
    """
    # return get_item_by_attrib(allLinks(), 'uniqueidentifier', what)
    return device.linkFromID(what)

def itemFromID(what):
    """return the item matching the ID.  Could be a device, a link, or a nic"""
    return device.itemFromID(what)


def destIP(srcDevice,dstDevice):
    """
    Find the destination IP address of the specified device, if going there from the source device.
    Many devices have multiple IP addresses.  If the IP is local, we go straight to it.  If it is on
    a different subnet, we get routed there.  This is a poor-man's DNS.
    Args:
        srcDevice:str - the hostname of the source device
        srcDevice:device - the device record of the source
        dstDevice:str - the hostname of the destination device
        dstDevice:device - the device record of the destination
    Returns:
        the string IP address of the nic that is local betwee the two devices, or the IP address on the destination 
        that is connected to its gateway IP.  None if the IP cannot be determined 
    """
    return device.destIP(srcDevice,dstDevice)

def sourceIP(src,dstIP):
    """
    Find the IP address to use when pinging the destination.  If the address is local, use the local nic.
    If the address is at a distance, we use the IP address associated with whatever route gets us there.
    Args:
        src:str - use the hostname as the source
        src:device - use src as the source device
        destIP:str - connect to this ip.  Eg: "192.168.1.1"
    return: an IP address string, or None
    """
    return device.sourceIP(src,dstIP)

def is_ipv4(string):
        """
        return True if the string is a valid IPv4 address.
        """
        return packet.is_ipv4(string)

def Ping(src, dest):
    """Generate a ping packet, starting at the srcdevice and destined for the destination device
    Args:
        src:srcDevice (also works with a hostname)
        dest:dstDevice (also works with a hostname)
        """
    device.Ping(src, dest)

def processPackets(killSeconds:int=20):
    """
    Loop through all packets, moving them along through the system
    Args: killseconds - the number of seconds to go before killing the packets.
    """
    killMilliseconds = killSeconds * 1000
    #here we loop through all packets and process them
    curtime = int(time.time() * 1000)
    for one in session.packetlist:
        #figure out where the packet is
        theLink = linkFromName(one['packetlocation'])
        if theLink is not None:
            #the packet is traversing a link
            one['packetDistance'] += 10 #traverse the link.  If we were smarter, we could do it in different chunks based on the time it takes to redraw
            if one['packetDistance'] > 100:
                #We have arrived.  We need to process the arrival!
                #get interface from link
                nicrec = theLink['SrcNic']
                if one['packetDirection'] == 2:
                    nicrec = theLink['DstNic']
                tNic = device.getDeviceNicFromLinkNicRec(nicrec)
                if tNic is None:
                    #We could not find the record.  This should never happen.  For now, blow up
                    print ("Bad Link:")
                    print (theLink)
                    print ("Direction = " + str(one['packetDirection']))
                    raise Exception("Could not find the endpoint of the link. ")
                #We are here.  Call a function on the nic to start the packet entering the device
                device.doInputFromLink(one, tNic)

        #If the packet has been going too long.  Kill it.
        if curtime - one['starttime'] > killMilliseconds:
            #over 20 seconds have passed.  Kill the packet
            one['status'] = 'failed'
            one['statusmessage'] = "Packet timed out"
    #When we are done with all the processing, kill any packets that need killing.
    cleanupPackets()

def cleanupPackets():
    """After processing packets, remove any "done" ones from the list."""
    for index in range(len(session.packetlist) - 1, -1, -1): 
        one = session.packetlist[index]
        match one['status']:
            case 'good':
                continue
            case 'failed':
                #We may need to log/track this.  But we simply remove it for now
                del session.packetlist[index]
                continue
            case 'done':
                #We may need to log/track this.  But we simply remove it for now
                del session.packetlist[index]
                continue
            case 'dropped':
                #packets are dropped when they are politely ignored by a device.  No need to log
                del session.packetlist[index]
                continue



def doTest():

    #mynet=choosePuzzlek('Level0-NeedsLink')
    mynet=choosePuzzle(3)
    print (mynet['name'])
    mydevice=deviceFromID('110');
    #print(mydevice)
    #mynic=nicFromName(mydevice,'eth0')
    mynic=nicFromID('112')
    #print(mynic)
    mylink=linkFromID('121')
    print(mylink)
