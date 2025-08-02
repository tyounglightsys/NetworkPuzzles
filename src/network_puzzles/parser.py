# This file will be the main parser.  We will pass commands to the puzzle through this.
# Most interaction with the puzzle, making changes or doing actions, will go through this
import logging
import sys
from . import device
from . import puzzle
from . import session
from . import packet


class Parser:
    def __init__(self):
        pass

    def get_puzzles(self, cmd, args):
        # We want to list all the items.
        pattern = None
        if len(args) > 0:
            pattern = args[0]
            try:
                # If it is just a number, look for that level. int(pattern)
                # throws a ValueError Exception if it fails, so we catch
                # that specific exception below.
                pattern = "Level" + str(int(pattern))
            except ValueError:
                # otherwise, leave the pattern alone
                pass
            if not pattern.startswith(".*"):
                pattern = r".*" + pattern
            if not pattern.endswith(".*"):
                pattern = pattern + r".*"

        pzs = puzzle.listPuzzles(pattern)
        val = pzs
        for a in pzs:
            session.print(a)
        return {"command": cmd, "value": val}

    def exit_app(self, code=0):
        sys.exit(code)

    def open_puzzle(self, cmd, args):
        val = None
        if len(args) == 1:
            val = puzzle.choosePuzzle(args[0])
        elif len(args) == 2:
            val = puzzle.choosePuzzle(args[0], args[1])
        else:
            print("loading: ")
        return {"command": cmd, "value": val}

    def parse(self, command: str, fromuser=True, fromundo=False):
        # We will make this a lot more interesting later.  For now, just do a very simple thing
        if command is not None and command.startswith("#"):
            #ignore comments.  Usually coming from the testing files
            return
        logging.debug(f"{command=}")
        session.packetstorm = False  # We are starting something new. It is false until we determine otherwise
        command = command.replace(
            ",", " "
        )  # replace commas with spaces.  This fixes x,y coords
        items = command.split()  # break at all whitespace
        if fromuser:
            session.history.append(command)  # add commands to the history
        if len(items) > 0:
            # we have stuff. Process it
            cmd = items[0].lower()
            args = items[1:]
            match cmd:
                case "create":
                    return self.create_something(args)
                case "help" | "?":
                    self.printhelp()
                case "history":
                    self.show_info(["history"])
                case "puzzles" | "search":
                    return self.get_puzzles(cmd, args)
                case "load" | "open":
                    val = self.open_puzzle(cmd, args)
                    # If debugging, show what we just loaded.
                    if logging.getLogger().level < logging.WARNING:
                        self.show_info(["puzzle"])
                    return val
                case "delete":
                    return self.delete_item(args)
                case "dhcp":
                    return self.do_dhcp(args)
                case "exit" | "quit" | "stop":
                    self.exit_app()
                case "ping":
                    return self.run_ping(args)
                case "replace":
                    return self.replace_something(args)
                case "show" | "list":
                    self.show_info(args)
                case "set":
                    return self.setvalue(args, fromuser)
                case "undo":
                    return self.try_undo()
                case "redo":
                    return self.try_redo()
                case _:
                    session.print(f"unknown: {command}")
        else:
            # If command is empty, do nothing. The prompt will just be reshown.
            pass

    def try_undo(self):
        if len(session.undolist) > 0:
            lastcmd = session.undolist.pop()
            if lastcmd.get("payload") is not None:
                # We deleted something and it needs to be re-added
                # determine what it is; a device or link
                payload = lastcmd.get("payload")
                session.print(f"restoring deleted {payload.get('hostname')}")
                if "DstNic" in payload:
                    # it is a link.
                    if not isinstance(session.puzzle.json["link"], list):
                        session.puzzle.json["link"] = [session.puzzle.json["link"]]
                    session.puzzle.json["link"].append(payload)
                    session.redolist.append(lastcmd)
                    return True
                else:
                    # it is a device
                    session.puzzle.json["device"].append(payload)
                    session.redolist.append(lastcmd)
                    return True
            # If we get here, we had no payload.
            # we need to run the backwards command
            self.parse(
                lastcmd.get("backwards"), False, True
            )  # specify this is from undo.  It does not get added to undo
            session.redolist.append(lastcmd)  # Put it onto the redo list
        else:
            session.print("Noting to undo")

    def try_redo(self):
        if len(session.redolist) > 0:
            lastcmd = session.redolist.pop()
            self.parse(lastcmd.get("forwards"), False, False)
            # The command is automatically added to the undo; through the parse.  We are done
        else:
            session.print("Noting to redo")

    def create_something(self, args):
        if len(args) == 0:
            session.print("You must specify something to create")
            session.print(
                "create link source_hostname [sourcenic] dest_hostname [destnic]"
            )
            session.print("create device devicetype x,y")
            session.print(
                "where devicetype is one of the known devices: pc, laptop, router, switch, firewall, etc."
            )
            return False
        item = args.pop(0).lower()
        if item == "link":
            return session.puzzle.createLink(args)
        elif item == "device":
            return session.puzzle.createDevice(args)

    def replace_something(self, args):
        if len(args) == 0:
            session.print("You must specify something to replace")
            return False
        if len(args) == 1:
            item = session.puzzle.link_from_name(args[0])
            if item is not None:
                # we have a link.  We can replace one of these
                session.add_undo_entry(
                    f"delete {item.get('hostname')}",
                    f"restore {item.get('hostname')}",
                    item,
                )
                session.puzzle.deleteItem(item.get("hostname"))
                linktype = item.get("linktype")
                if linktype == "broken":
                    linktype = "normal"  # we replace broken links
                session.puzzle.createLink(
                    [
                        item["SrcNic"]["hostname"],
                        item["SrcNic"]["nicname"],
                        item["DstNic"]["hostname"],
                        item["DstNic"]["nicname"],
                    ],
                    linktype,
                )
                session.add_undo_entry(
                    f"create link {item['SrcNic']['hostname']} {item['SrcNic']['nicname']} {item['DstNic']['hostname']} {item['DstNic']['nicname']}",
                    f"delete {item.get('hostname')}",
                )
                return True
            item = session.puzzle.device_from_name(args[0])
            if item is not None:
                # We have a device. We can replace one of these.
                raise NotImplementedError
            else:  # it is something that does not exist
                raise ValueError(f"Not a valid item: {args[0]}")

    def printhelp(self):
        session.print("--- CLI Help ---")
        session.print(
            "create link source destination - create a link between two devices.  example: create link pc0 net_switch0"
        )
        session.print("delete [item] - delete a device or link")
        session.print("dhcp [item] - have that device do a DHCP or all devices do a DHCP request")
        session.print("help - show this page")
        session.print("history - see the commands you typed this session")
        session.print("load - load a puzzle.  Example: load 1 | load Level0_Ping")
        session.print("quit - exit the cli")
        session.print(
            "search [info] - list the puzzles matching the info.  Example: search DHCP | search 1"
        )
        session.print(
            "set - change a value.  Example: set pc0 gateway | set pc0 dhcp true"
        )
        session.print(
            "show [item] - show information about an item.  Example: show | show pc0 | show tests | show history"
        )
        session.print(
            "ping [host1] [host2] - ping from one host to the other.  Example: ping pc0 pc1"
        )

    def run_ping(self, args):
        if len(args) != 2:
            session.print(
                "invalid ping command: usage: ping source_hostname destination_hostname"
            )
            session.print(" example: ping pc0 pc1")
            return False

        shost = session.puzzle.device_from_name(args[0])
        dhost = session.puzzle.device_from_name(args[1])
        if shost is None:
            session.print(f"No such host: {args[0]}")
            return False
        if dhost is None:
            session.print("No such host: " + args[1])
            return False
        # if we get here, we are ready to try to ping.
        session.print(f"PING {args[1]} from {args[0]}")
        device.Ping(shost, dhost)
        # FIXME: This only shows that the ping command was successfully
        # initiated, not that it was itself successful.
        return True

    def do_dhcp(self, args):
        if len(args) == 0:
            #It was simply: dhcp.  We assume 'all'
            args.append('all')
        if args[0] == 'all':
            for one in session.puzzle.all_devices():
                if 'hostname' in one:
                    device.doDHCP(one.get('hostname'))
        else:
            device.doDHCP(args[0])


    def delete_item(self, args):
        if len(args) == 0:
            session.print("invalid delete command: usage: delete item")
            session.print(" example: delete pc0")
            session.print(" example: delete pc0_link_net_switch0")
            return False
        logging.debug(f"parser.Parser.delete_item({args[0]})")
        target_device = session.puzzle.device_from_name(args[0])
        if target_device is None:
            target_device = session.puzzle.link_from_name(args[0])
        if target_device is None:
            session.print(f"Cannot delete: No such item {args[0]}")
            return False
        # check to see if we are able to delete.  Is it locked?
        # We will need to check for that later after the tests are done.
        return session.puzzle.deleteItem(args[0])

    def show_info(self, args):
        # list the hosts.  Or, show information about a specifici host
        if len(args) == 0:
            # Just the show command.  List all the devices
            session.print(session.puzzle.json.get("name"))
            devicelist = [d for d in session.puzzle.devices]
            if len(devicelist) > 0:
                session.print("----devices----")
            for one in devicelist:
                session.print(one["hostname"])
            linklist = [k for k in session.puzzle.links]
            if len(linklist) > 0:
                session.print("----links----")
            for one in linklist:
                if one is not None:
                    session.print(one["hostname"])

        if len(args) == 1:
            thedevice = session.puzzle.device_from_name(args[0])
            if thedevice is not None:
                # we have a valid device.  Show information about the device
                session.print("----Device----")
                session.print(f"hostname: {thedevice['hostname']}")
                if "poweroff" in thedevice and thedevice["poweroff"].lower() == "true":
                    session.print(f"poweroff: {thedevice['poweroff']}")
                if "isdhcp" in thedevice and thedevice["isdhcp"].lower() == "true":
                    session.print(f"DHCP server: {thedevice['isdhcp']}")
                session.print(f"gateway: {thedevice['gateway']['ip']}")
                for onestring in device.allIPStrings(thedevice, True, True):
                    session.print(onestring)
                return
            thedevice = session.puzzle.link_from_name(args[0])
            if thedevice is not None:
                # we have a valid link.  Show information about the link
                session.print("----Link----")
                session.print(f"name: {thedevice['hostname']}")
                session.print(f"type: {thedevice['linktype']}")
                session.print(
                    f"source: {thedevice['SrcNic']['hostname']} - {thedevice['SrcNic']['nicname']}"
                )
                session.print(
                    f"dest: {thedevice['DstNic']['hostname']} - {thedevice['DstNic']['nicname']}"
                )
                return
            if args[0].lower() == "tests":
                session.print("--Tests--")
                for onetest in session.puzzle.all_tests():
                    session.print(
                        f"source: {onetest.get('shost')} test: {onetest.get('thetest')}  dest: {onetest.get('dhost')} status: {onetest.get('completed', 'False')}"
                    )
                return
            if args[0].lower() == "puzzle":
                session.print("----Puzzle----")
                session.print(session.puzzle.json.get("name"))
                session.print(session.puzzle.json.get("en_title"))
                session.print(session.puzzle.json.get("en_message"))
                self.show_info([])
                self.show_info(["tests"])
                return
            if args[0].lower() == "history":
                for oneline in session.history:
                    session.print(oneline)
                return
            if args[0].lower() == "undo":
                for oneline in session.undolist:
                    session.print(oneline["forwards"])
                return
            if args[0].lower() == "redo":
                for oneline in session.redolist:
                    session.print(oneline["backwards"])
                return
            session.print(f"No such host {args[0]}")

    def set_dhcp_value(self, dev_obj, value):
        if not device.servesDHCP(dev_obj.json):
            session.print(f"{dev_obj.hostname} can not be a dhcp server")
            return False
        pastvalue = "false"
        if dev_obj.is_dhcp:
            pastvalue = "true"
        if value.lower() in ("true", "yes"):
            dev_obj.is_dhcp = True
            session.add_undo_entry(
                f"set {dev_obj.hostname} isdhcp true",
                f"set {dev_obj.hostname} isdhcp {pastvalue}",
            )
        else:
            dev_obj.is_dhcp = False
            session.add_undo_entry(
                f"set {dev_obj.hostname} isdhcp false",
                f"set {dev_obj.hostname} isdhcp {pastvalue}",
            )
        session.print(
            f"Defining {dev_obj.hostname} 'isdhcp' to {dev_obj.json.get('isdhcp')}"
        )

    def set_gateway_value(self, dev_obj, value):
        # we really need to do some type checking.  It should be a valid ipv4 or ipv6 address
        if packet.is_ipv4(value) or packet.is_ipv6(value):
            session.add_undo_entry(
                f"set {dev_obj.hostname} gateway {value}",
                f"set {dev_obj.hostname} gateway {dev_obj.json['gateway']['ip']}",
            )
            dev_obj.json["gateway"]["ip"] = value
            session.print(
                f"Setting {dev_obj.hostname} gateway: {dev_obj.json['gateway']['ip']}"
            )
        else:
            session.print(f"invalid address: {value}")
            return False

    def set_ip_value(self, dev_obj, nicname, value, fromuser=True):
        # we should be setting the IP address.
        theparts = value.split("/")
        ip = theparts[0]
        mask = ""
        if len(theparts) > 1:
            mask = theparts[1]
        if packet.is_ipv4(ip) or packet.is_ipv6(ip):
            # we are good to go.
            # get the nic and interface.
            interface = dev_obj.interface_from_name(nicname)
            nic = dev_obj.nic_from_name(nicname)
            if interface is not None:
                # we found it.  Change the IP if we are able
                if fromuser and nic.get('usesdhcp') == "True":
                    #The user cannot set the IP manually if the NIC is set to use DHCP
                    session.print(f"{nicname} is set for DHCP.  Cannot change it manually.")
                    return
                # we should have some better syntax checking here.
                if mask == "":
                    mask = interface["myip"]["mask"]
                session.add_undo_entry(
                    f"set {dev_obj.hostname} {nicname} {ip}/{mask}",
                    f"set {dev_obj.hostname} {nicname} {interface['myip']['ip']}/{interface['myip']['mask']}",
                )
                interface["myip"]["ip"] = ip
                interface["myip"]["mask"] = mask
                print(
                    f"Setting {dev_obj.hostname} {nicname} to: {interface['myip']['ip']} / {interface['myip']['mask']}"
                )
                session.puzzle.check_local_IP_test(dev_obj.json)
            else:
                session.print(f"Could not find Nic: {nicname}")
                return False
        else:
            session.print(f"Not a valid IP: {ip}")
            return False

    def set_position_value(self, dev_obj, x_in, y_in):
        logging.debug("set_position_value entry")
        if session.puzzle.item_is_locked(dev_obj.hostname, "LockLocation"):
            session.print(f"Device cannot be moved: {dev_obj.hostname}")
            return False
        x = int(x_in.replace(",", ""))
        y = int(y_in.replace(",", ""))
        if x + 0 and y > 0:
            pastvalue = dev_obj.json.get("location")
            session.add_undo_entry(
                f"set {dev_obj.hostname} location {x},{y}",
                f"set {dev_obj.hostname} location {pastvalue}",
            )
            session.print(f"Setting position of {dev_obj.hostname} to {x},{y}")
            dev_obj.json["location"] = f"{x},{y}"
            # TODO: We need a callback here to tell te gui to redraw. - we just moved a device
            # if we just moved a 'lost' switch, we can draw it
            if dev_obj.is_invisible:
                dev_obj.is_invisible = False
                # TODO: We need a callback here to tell the gui to redraw.
            logging.debug(f"{dev_obj.is_invisible=}")
            # if any of the links connected to the switch were hidden/invisible, draw them
            for onenic in dev_obj.all_nics():
                onelink = device.linkConnectedToNic(onenic)
                if (
                    onelink is not None
                    and onelink.get("isinvisible", "").lower() == "true"
                ):
                    onelink["isinvisible"] = "False"
                    logging.debug(f"{onelink.get('isinvisible')=}")
                    # TODO: We need a callback here to tell the gui to redraw.

    def set_power_value(self, dev_obj, value):
        pastvalue = "on"
        # if dev_data.get("poweroff") == "True":
        if not dev_obj.powered_on:
            pastvalue = "off"
        if value.lower() == "off":
            session.add_undo_entry(
                f"set {dev_obj.hostname} power off",
                f"set {dev_obj.hostname} power {pastvalue}",
            )
            dev_obj.powered_on = True
            session.puzzle.mark_test_as_completed(
                None, dev_obj.hostname, "DeviceIsFrozen", ""
            )
        else:
            session.add_undo_entry("set power on", f"set power {pastvalue}")
            dev_obj.powered_on = False
        # Additional call for special UI handling.
        session.ui.update_power_status(dev_obj.hostname)
        session.print(
            f"Defining {dev_obj.hostname} 'poweroff' to {dev_obj.json.get('poweroff')}"
        )

    def setvalue(self, args, fromuser=True):
        # set a value on a device.
        # right now, we have something like: set pc0 poweroff true

        # Ensure enough args.
        if len(args) < 2:
            raise ValueError(f"Not enough args in command: {args}")

        # Ensure valid device name.
        name = args[0].lower()
        prop = args[1].lower()
        values = args[2:]
        dev_data = session.puzzle.device_from_name(name)
        if dev_data is None:
            raise NameError(f"Device not found: {name}")

        dev_obj = device.Device(dev_data)

        # Ensure device is visible.
        if dev_obj.is_invisible:
            can_continue = False
            for onenic in dev_obj.all_nics():
                onelink = device.linkConnectedToNic(onenic)
                if onelink is not None and (
                    onelink.get("isinvisible") == "false"
                    or onelink.get("isinvisible") == "False"
                ):
                    can_continue = True
                if onelink is not None and "isinvisible" not in onelink:
                    can_continue = True
            if not can_continue:
                session.print(
                    f"{dev_obj.hostname} is lost and you cannot work with it until it is found"
                )
                return False

        logging.debug(f"{name=}; {prop=}, {values=}")
        match prop:
            case "power":
                self.set_power_value(dev_obj, values[0])
            case "poweroff":
                if len(values) == 0:
                    self.set_power_value(dev_obj, "off")
                else:
                    self.set_power_value(dev_obj, values[0])
            case "poweron":
                self.set_power_value(dev_obj, "on")
            case "dhcp" | "isdhcp":
                self.set_dhcp_value(dev_obj, values[0])
            case "gateway" | "gw":
                self.set_gateway_value(dev_obj, values[0])
            case "location" | "position" | "pos":
                self.set_position_value(dev_obj, values[0], values[1])
            case _:
                # Set IP address of NIC, where nicname == prop.
                if (
                    prop.startswith("eth")
                    or prop.startswith("wan")
                    or prop.startswith("wlan")
                    or prop.startswith("management")
                ):
                    self.set_ip_value(dev_obj, prop, values[0],fromuser)
