#!/usr/bin/python3
# All the functions needed for reading the EduNetwork Puzzle file
# And getting information from it
import json
import copy
import re
import os
import logging
from packaging.version import Version

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

    @property
    def default_help_level(self):
        match self.json.get("startinghelplevel", "full"):
            case "none":
                help_level = 0
            case "basic":
                help_level = 1
            case "hints":
                help_level = 2
            case "full":
                help_level = 3
        return help_level

    @property
    def devices(self):
        """Generator to yield all devices in puzzle."""
        for dev in self.json.get("device", []):
            if isinstance(dev, str):
                yield self.json.get("device")
                break
            yield dev

    @property
    def links(self):
        """Generator to yield all devices in puzzle."""
        for lnk in self.json.get("link", []):
            if isinstance(lnk, str):
                yield self.json.get("link")
                break
            yield lnk

    @property
    def uid(self):
        return f"{self.json.get('level')}.{self.json.get('sortorder')}"

    def all_devices(self):
        """
        Return a list that contains all devices in the puzzle.
        """
        return self._get_items("device")

    def all_links(self):
        """
        Return a list that contains all links in the puzzle.
        """
        return self._get_items("link")

    def all_tests(self, hostname=None):
        tests = []
        for test in self._get_items("nettest"):
            if hostname is None:
                tests.append(test)
            else:
                if test.get("shost") == hostname:
                    tests.append(test)
        return tests

    def all_puzzle_IPs(self):
        iplist = list()
        for onedevice in self.devices:
            if onedevice:
                iplist.extend(device.DeviceIPs(onedevice, True))
        return iplist

    def commands_from_tests(self, hostname=None):
        commands = list()
        for test in self.all_tests(hostname):
            # print(f"checking test: {onetest.get('shost')} {onetest.get('dhost')} {onetest.get('thetest')} - {onetest.get('completed',False)}")
            if test.get("completed", False):
                continue
            # We are looking at the tests corresponding to the host in question:
            # NeedsLocalIPTo, NeedsDefaultGW, NeedsLinkToDevice, NeedsRouteToNet,
            # NeedsUntaggedVLAN, NeedsTaggedVLAN, NeedsForbiddenVLAN,
            # SuccessfullyPings, SuccessfullyPingsAgain, SuccessfullyArps, SuccessfullyDHCPs, HelpRequest, ReadContextHelp, FailedPing,
            # DHCPServerEnabled, SuccessfullyTraceroutes, SuccessfullyPingsWithoutLoop,
            # LockAll, LockIP, LockRoute, LockNic, LockDHCP, LockGateway, LockLocation,
            # LockVLANsOnHost, LockNicVLAN, LockInterfaceVLAN, LockVLANNames,
            # DeviceIsFrozen, DeviceBlowsUpWithPower, DeviceNeedsUPS, DeviceNICSprays,
            match test.get("thetest"):
                case "NeedsLinkToDevice":
                    # Could be an existing link to be replaced or a missing link
                    # to be created. Plus, the link name could be in reverse order.
                    link_name = f"{test.get('shost')}_link_{test.get('dhost')}"
                    link = self.link_from_name(link_name)
                    if not link:
                        # Reverse the link hostname and try again.
                        link_name = f"{test.get('dhost')}_link_{test.get('shost')}"
                        link = self.link_from_name(link_name)
                    if link in self.links:
                        # Link exists, include option to replace it.
                        commands.append(f"replace {link_name}")
                    else:
                        commands.append(
                            f"create link {test.get('shost')} {test.get('dhost')}"
                        )
                case (
                    "SuccessfullyPings"
                    | "SuccessfullyPingsAgain"
                    | "SuccessfullyPingsWithoutLoop"
                ):
                    commands.append(f"ping {test.get('shost')} {test.get('dhost')}")
                case "DeviceIsFrozen" | "DeviceBlowsUpWithPower" | "DeviceNeedsUPS":
                    if device.powerOff(hostname):
                        commands.append(f"set {test.get('shost')} power on")
                    else:
                        commands.append(f"set {test.get('shost')} power off")
        tdevice = self.device_from_name(hostname)
        if tdevice is not None and device.canUseDHCP(hostname):
            commands.append(f"dhcp {hostname}")
        return commands

    def _get_items(self, item_type: str):
        """
        Return a list of the given item_type ('link', 'device', 'nettest').
        """
        items = []
        only_one_item = False
        for item in self.json.get(item_type, []):
            # Some item attribs are single-item dicts. Convert if necessary.
            if not isinstance(item, dict):
                only_one_item = True
                item = self.json.get(item_type)
            match item_type:
                case "link" | "device":
                    if "hostname" in item:
                        items.append(item)
                case "nettest":
                    items.append(item)
            if only_one_item:
                break  # stop iterating through dict keys
        return items

    def arp_lookup(self, ipaddr):
        return device.globalArpLookup(ipaddr)

    def device_from_name(self, name):
        return self._item_by_attrib(self.devices, "hostname", name)

    def device_from_uid(self, uid):
        uid = str(uid)  # ensure not an integer
        return self._item_by_attrib(self.devices, "uniqueidentifier", uid)

    def device_is_critical(self, name):
        test_devices = set()
        for test in self.all_tests():
            for h in ("shost", "dhost"):
                host = test.get(h)
                if host:
                    test_devices.add(host)
        return name in test_devices

    def device_is_frozen(self, thost):
        for test in self.all_tests():
            if (
                test.get("shost") == thost.get("hostname")
                and test.get("thetest") == "DeviceIsFrozen"
            ):
                if test.get("completed"):
                    return False
                else:
                    return True
        return False

    def has_test_been_completed(self, shost, dhost, whattocheck):
        for test in self.all_tests():
            if (
                test.get("shost") == shost
                and test.get("dhost") == dhost
                and test.get("thetest") == whattocheck
            ):
                # the test matches, return true only if 'completed' is set to true
                return test.get("completed", False)
        return False

    def check_local_IP_test(self, shost):
        """Check to see if there is a test we need to check for completion"""
        logging.debug(f"{shost.get('hostname')=}")
        for test in self.all_tests():
            if test.get("completed"):
                # only check tests which are not completed
                continue
            if (
                test.get("shost") == shost.get("hostname")
                and test.get("thetest") == "NeedsLocalIPTo"
            ):
                # We have a test we want to check.
                # verify we do not have duplicate IPs.
                # verify that the IP is local to the one on the target device.
                dhost = self.device_from_name(test.get("dhost"))
                allIPList = self.all_puzzle_IPs()
                if dhost is None:
                    continue
                dstlist = device.DeviceIPs(dhost, True)
                srclist = device.DeviceIPs(shost, True)
                for one_s_ip in srclist:
                    # make sure we do not have a duplicate IP
                    if allIPList.count(one_s_ip) > 1:
                        continue  # There is a duplicate.  It does not count as success.
                    for one_d_ip in dstlist:
                        # Now, check to see if the source is in the destination network
                        if one_d_ip != one_s_ip and one_s_ip in one_d_ip.network:
                            # It is true.
                            test["completed"] = True
                            test["acknowledged"] = False
                            test["message"] = (
                                f"{shost.get('hostname')} has local IP to {dhost.get('hostname')}"
                            )

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

    def item_is_locked(self, shost, whattocheck, dhost=None):
        for test in self.all_tests(shost):
            thetest = test.get("thetest")
            if thetest == "LockAll":
                return True
            if thetest == whattocheck and whattocheck == "LockVlanNames":
                return True
            if thetest == whattocheck and whattocheck == "LockVLANsOnHost":
                return True
            if thetest == whattocheck and dhost and test.get("dhost") == dhost:
                # if the source (hostname) and dest (, ping_desthostname, nic, etc) also match.
                return True
        return False

    def link_from_devices(self, srcDevice, dstDevice):
        """return a link given the two devices at either end
        Args:
            srcDevice:Device - the device itself
            srcDevice:str - the hostname of the device
            dstDevice:device - the device itself
            dstDevice:str - the hostname of the device
        Returns: a link record or None
        """
        srcstr = ""
        dststr = ""
        if isinstance(srcDevice, str):
            srcstr = srcDevice
        else:
            if "hostname" in srcDevice:
                srcstr = srcDevice.get("hostname")
        if isinstance(dstDevice, str):
            dststr = dstDevice
        else:
            if "hostname" in dstDevice:
                dststr = dstDevice.get("hostname")
        # Now we should have srcstr and dststr set.  Use them to concoct a link name
        # The link name looks like: pc0_link_pc1
        result = session.puzzle.link_from_name(srcstr + "_link_" + dststr)
        if result is not None:
            logging.warning(f"link exists, {result.get('hostname')}")
            return result
        result = session.puzzle.link_from_name(dststr + "_link_" + srcstr)
        if result is not None:
            logging.warning(f"link exists, {result.get('hostname')}")
            return result
        # if we get here, we could not find it. Return none
        return None

    def link_from_name(self, name):
        return self._item_by_attrib(self.links, "hostname", name)

    def link_from_uid(self, uid):
        return self._item_by_attrib(self.links, "uniqueidentifier", uid)

    def mark_test_as_completed(self, shost, dhost, whattocheck, message):
        for onetest in self.all_tests():
            if (
                onetest.get("shost") == shost
                and onetest.get("dhost") == dhost
                and onetest.get("thetest") == whattocheck
            ) or (
                onetest.get("dhost") == dhost
                and onetest.get("thetest") == whattocheck
                and whattocheck == "DeviceIsFrozen"
            ):
                # if the test has never been completed
                if not onetest.get("completed", False):
                    onetest["completed"] = True
                    onetest["acknowledged"] = False
                    onetest["message"] = message
                    # print(f"Debug: Marking as done: {onetest.get('shost')} {onetest.get('dhost')} {onetest.get('thetest')}")
                return True  # no need to continue looping through other tests

    def nic_from_uid(self, uid):
        """find the network card from the id
        Args: uid: int - the device id for the nic you are looking for
        Notes:
            Each component on the network has a unique ID.  PCs can change names, so we do not assume host-names are unique.
            Thus, for a network link (ethernet cable, wireless, etc) to know what two devices it is connecting, we use the ID
        """
        for d in self.devices:
            if d:
                item = self._item_by_attrib(d.get("nic"), "uniqueidentifier", uid)
                if item:
                    return item
        return None

    def firstFreeNic(self, deviceRec):
        """find the first unused network card
        Args: deviceRec: the device record
        returns: the first port, eth or whatnot that is not attached to something.  None if no port can be found
        """
        for onenic in deviceRec.get("nic"):
            if onenic.get("nictype")[0] == "lo":
                continue  # skip loopback devices
            if onenic.get("nictype")[0] == "management_interface":
                continue  # skip management_interface devices
            match onenic.get("nictype")[0]:
                case "port" | "wport" | "eth" | "wan" | "wlan":
                    tlink = device.linkConnectedToNic(onenic)
                    if tlink is None:
                        return onenic
            # if the nic type is not one of those, then do not give it as an option.
        return None

    def set_all_device_nic_macs(self):
        for oneDevice in self.devices:
            if oneDevice:
                if not isinstance(oneDevice["nic"], list):
                    oneDevice["nic"] = [oneDevice["nic"]]
                for oneNic in oneDevice["nic"]:
                    oneNic = Nic(oneNic).ensure_mac()

    def _item_by_attrib(self, items: iter, attrib: str, value: str) -> dict | None:
        # Returns first match; i.e. assumes only one item in list matches given
        # attribute. It also assumes that 'items' is a list of dicts or json data.
        for item in items:
            if item and item.get(attrib) == value:
                return item

    def deleteItem(self, itemToDelete: str):
        existing_device = self.device_from_name(itemToDelete)
        if existing_device:
            if session.puzzle.device_is_critical(itemToDelete):
                session.print(
                    f"Cannot delete {itemToDelete}.  The puzzle has it locked."
                )
                return False
            # We need to find any links connected to this device and delete them
            for onenic in device.Device(existing_device).all_nics():
                onelink = device.linkConnectedToNic(onenic)
                if onelink is not None:
                    self.deleteItem(onelink.get("hostname"))
            session.print(f"Deleting: {itemToDelete}")
            session.ui.delete_item(existing_device)
            session.add_undo_entry(
                f"delete {itemToDelete}", f"restore {itemToDelete}", existing_device
            )  # make entry using payload
            if isinstance(self.json.get("device"), dict):
                # Replace single-item dict with an empty list.
                self.json["device"] = []
            elif isinstance(self.json.get("device"), list):
                idx = self.json["device"].index(existing_device)
                del self.json["device"][idx]
            return True
        existing_link = self.link_from_name(itemToDelete)
        if existing_link:
            session.print(f"Deleting: {itemToDelete}")
            # Additional call for special UI handling.
            session.ui.delete_item(existing_link)
            session.add_undo_entry(
                f"delete {itemToDelete}", f"restore {itemToDelete}", existing_link
            )  # make entry using payload
            if isinstance(self.json.get("link"), dict):
                # Replace single-item dict with an empty list.
                self.json["link"] = []
            elif isinstance(self.json.get("link"), list):
                # Delete item from list.
                idx = self.json["link"].index(existing_link)
                del self.json["link"][idx]
            return True
        return False

    def issueUniqueIdentifier(self):
        availableval = self.json.get("uniqueidentifier")
        nextval = str(int(availableval) + 1)
        self.json["uniqueidentifier"] = nextval
        return availableval

    def createNIC(self, thedevicejson, nictype):
        thedevice = device.Device(thedevicejson)
        count = 0
        while (thedevice.nic_from_name(f"{nictype}{count}")) is not None:
            count = count + 1
        newnicname = f"{nictype}{count}"
        newid = self.issueUniqueIdentifier()
        newnic = {
            "nictype": [f"{nictype}", f"{nictype}"],
            "nicname": newnicname,
            "myid": {
                "hostid": thedevice.uid,
                "nicid": newid,
                "hostname": thedevice.hostname,
                "nicname": newnicname,
            },
            "uniqueidentifier": newnicname,
            "usesdhcp": "False",
            "encryptionkey": None,
            "ssid": None,
            "interface": [
                {
                    "nicname": newnicname,
                    "myip": {
                        "ip": "0.0.0.0",
                        "netmask": "0.0.0.0",
                        "gateway": "0.0.0.0",
                    },
                }
            ],
        }
        thedevicejson["nic"].append(newnic)
        return newnic

    def createDevice(self, args):
        if len(args) != 3:
            logging.error("createDevice: invalid number of arguments.")
            return
        device_type = args[0]
        x = args[1]
        y = args[2]
        count = 0
        while self.device_from_name(f"{device_type}{count}") is not None:
            count = count + 1
        newdevicename = f"{device_type}{count}"
        newid = self.issueUniqueIdentifier()
        newdevice = {
            "hostname": newdevicename,
            "uniqueidentifier": newid,
            "location": f"{x},{y}",
            "mytype": device_type,
            "isdns": "False",
            "isdhcp": "False",
            "gateway": {
                "ip": "0.0.0.0",
                "netmask": "0.0.0.0",
            },
            "nic": list(),
        }
        if device_type not in {"tree", "fluorescent"}:
            self.createNIC(newdevice, "lo")
        if device_type in {"net_switch", "net_hub"}:
            self.createNIC(newdevice, "management_interface")
            for a in range(8):
                self.createNIC(newdevice, "port")
        if device_type == "pc":
            for a in range(2):
                self.createNIC(newdevice, "eth")
        if device_type == "laptop":
            self.createNIC(newdevice, "eth")
            self.createNIC(newdevice, "wlan")
        if device_type == "wbridge":
            self.createNIC(newdevice, "wlan")
            for a in range(4):
                self.createNIC(newdevice, "wport")
        if device_type == "wap":
            self.createNIC(newdevice, "management_interface")
            self.createNIC(newdevice, "port")
            for a in range(6):
                self.createNIC(newdevice, "wport")
        if device_type == "wrepeater":
            self.createNIC(newdevice, "wport")
            self.createNIC(newdevice, "wlan")
        if device_type == "wrouter":
            self.createNIC(newdevice, "management_interface")
            for a in range(4):
                self.createNIC(newdevice, "port")
            for a in range(8):
                self.createNIC(newdevice, "wport")
            self.createNIC(newdevice, "vpn")
            self.createNIC(newdevice, "wan")
        if device_type == "firewall":
            self.createNIC(newdevice, "eth")
            self.createNIC(newdevice, "wan")
        if device_type in {"cellphone", "tablet"}:
            self.createNIC(newdevice, "wlan")

        self.json["device"].append(newdevice)
        session.print(f"Creating new device: {newdevicename}")
        # Additional call for special UI handling.
        session.ui.create_device(newdevice)

    def createLink(self, args, linktype="normal") -> bool:
        """returns False on error, True if successful, None if unhandled"""
        # we should have a source device, and an optional src nic, and a dest device and an optional dest nic
        if len(args) == 0:
            session.print("Error.  You must pass arguments to createLink")
            return False
        # the first item must be a hostname for the first device
        sdevicename = args.pop(0)
        sdevice = session.puzzle.device_from_name(sdevicename)
        if sdevice is None:
            session.print(f"Error: no such device: {sdevicename}")
            return False
        # The second item might be a nic name, or the second device.
        snicname = args[0]
        snic = device.Device(sdevice).nic_from_name(snicname)
        if snic is None:
            snicname = ""
            if session.puzzle.device_from_name(args[0]) is None:
                # the nic failed to match, and it was not a valid host.
                if len(args) > 1:
                    # we are not sure if it is a devicename or a port.
                    session.print(f"Could not match: {args[0]}")
                    return False

        else:
            args.pop(
                0
            )  # get rid of it. if it is none, we use the arg as the dest hostname
        ddevicename = args.pop(0)
        ddevice = session.puzzle.device_from_name(ddevicename)
        if ddevice is None:
            session.print(f"Error no such device {ddevicename}")
            return False
        dnicname = ""
        dnic = None
        if len(args) > 0:
            dnic = device.Device(ddevice).nic_from_name(args[0])
            if dnic is not None:
                dnicname = args[0]
            else:
                session.print(f"Could not find nic: {args[0]}")
                return False
        # If the snic and dnics are not set, find an available one.
        if snic is None:
            snic = self.firstFreeNic(sdevice)
            if snic is not None:
                snicname = snic.get("nicname")
        if dnic is None:
            dnic = self.firstFreeNic(ddevice)
            if dnic is not None:
                dnicname = dnic.get("nicname")  # this was mainly for debugging
        # print(f"trying to make a link from {sdevicename} {snicname} to {ddevicename} {dnicname}")
        existinglink = self.link_from_devices(sdevice, ddevice)
        if existinglink is not None:
            session.print(f"Link already exists: {existinglink['hostname']}")
            return False
        # verify the port types match
        ismatch = False
        snictype = snic.get("nictype")[0]
        dnictype = dnic.get("nictype")[0]
        if (snictype == "wlan" or snictype == "wport") and (
            dnictype == "wlan" or dnictype == "wport"
        ):
            ismatch = True
        if (snictype == "port" or snictype == "eth" or snictype == "wan") and (
            dnictype == "port" or dnictype == "eth" or dnictype == "wan"
        ):
            ismatch = True
        # if we get here, we should have all the pieces.
        if ismatch:
            newlink = {}
            newlink["hostname"] = sdevicename + "_link_" + ddevicename
            newlink["linktype"] = (
                linktype  # should be "normal", "broken", or "wireless"
            )
            newlink["uniqueidentifier"] = session.puzzle.issueUniqueIdentifier()
            newlink["SrcNic"] = copy.copy(snic.get("myid"))
            newlink["DstNic"] = copy.copy(dnic.get("myid"))
            if not isinstance(self.json.get("link"), list):
                self.json["link"] = [self.json.get("link")]
            self.json["link"].append(newlink)
            session.print(f"Created link: {newlink['hostname']}")
            device.mark_test_as_completed(
                sdevicename,
                ddevicename,
                "NeedsLinkToDevice",
                f"Solved: Create link between {sdevicename} and {ddevicename}",
            )
            device.mark_test_as_completed(
                ddevicename,
                sdevicename,
                "NeedsLinkToDevice",
                f"Solved: Create link between {sdevicename} and {ddevicename}",
            )
            # Additional call for special UI handling.
            session.ui.create_link(newlink)
            return True
        else:
            session.print(f"Cannot connect ports of type: {snictype} and {dnictype}")
            return False

    def is_puzzle_done(self):
        """Report back to see if all the tests have been completed."""
        for onetest in self.all_tests():
            if not onetest.get("completed", False):
                return False
        return True


def read_json_file(file_path):
    """
    Reads a JSON file and returns the data as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The JSON data as a Python dictionary, or None if an error occurs.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {file_path}")
        return None


def matches_filter(name: str, pattern: str | None) -> bool:
    if pattern is None:
        return True
    elif re.match(pattern, name, re.IGNORECASE):
        return True
    else:
        return False


def sort_session_puzzles():
    session.puzzlelist.sort(
        key=lambda x: (
            Version(x["EduNetworkBuilder"]["Network"]["level"]),
            Version(x["EduNetworkBuilder"]["Network"]["sortorder"]),
        )
    )


def filter_items(items: list, pattern: str, json_files: bool = False) -> list:
    filtered_items = []
    for item in items:
        if not json_files:
            name = item["EduNetworkBuilder"]["Network"]["name"]
        else:
            name = re.sub(r"\.json", "", item)
        if matches_filter(name, pattern):
            filtered_items.append(name)
    return filtered_items


def listPuzzlesFromDisk(regex_pattern: str = None):
    directory_path = "src/network_puzzles/resources/puzzles"
    files = [
        f
        for f in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, f))
    ]
    return filter_items(files, regex_pattern, json_files=True)


def listPuzzles(regex_pattern: str = None):
    if len(session.puzzlelist) == 0:
        readPuzzle()
    sort_session_puzzles()
    return filter_items(session.puzzlelist, regex_pattern)


def readPuzzle():
    """Read in the puzzles from the various .json files"""
    if len(session.puzzlelist) == 0:
        allfiles = listPuzzlesFromDisk("Level.*")
        for one in allfiles:
            # We stripped off the ".json" from the name, so we need to add it back
            file_path = "src/network_puzzles/resources/puzzles/" + one + ".json"
            oneentry = read_json_file(file_path)
            oneentry["EduNetworkBuilder"]["Network"]["name"] = one
            session.puzzlelist.append(oneentry)
            # print("loading: " + one)
        sort_session_puzzles()
        session.undolist = (
            list()
        )  # get rid of undo history; it would not apply to the new puzzle
        session.redolist = (
            list()
        )  # get rid of redo history; it would not apply to the new puzzle


def choosePuzzleFromName(what: str):
    """
    Choose a puzzle using the puzzle name.
    Args:
        what: string - The puzzle name, matching case and everything, of the puzzle we want to select
    """
    readPuzzle()
    # print ("Length of puzzleslist: " + str(len(puzzlelist)))

    for one in session.puzzlelist:
        if one["EduNetworkBuilder"]["Network"]["name"] == what:
            return copy.deepcopy(one["EduNetworkBuilder"]["Network"])


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
        # We have a filter.  We need to try to look up the item from the filtered list
        filteredList = listPuzzles(filter)
        if len(filteredList) > 0:
            # this means it is a valid filter. Try to use it.
            try:
                what = filteredList[int(what)]
            except Exception:
                # It did not work.  Ignore the filter.
                1  # This command does nothing.  It allows us to have an exception that does not blow anything up

    if isinstance(what, int):
        puz = copy.deepcopy(session.puzzlelist[what]["EduNetworkBuilder"]["Network"])
    else:
        try:
            # if the int(what) fails, we treat it as a name
            puz = copy.deepcopy(
                session.puzzlelist[int(what)]["EduNetworkBuilder"]["Network"]
            )
        except Exception:
            puz = choosePuzzleFromName(what)
    if puz is not None:
        session.print("Loaded: " + puz["name"])
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
