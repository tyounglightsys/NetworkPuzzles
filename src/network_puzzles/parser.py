# This file will be the main parser.  We will pass commands to the puzzle through this.
# Most interaction with the puzzle, making changes or doing actions, will go through this
import logging
import sys
import copy
import ipaddress

from . import device
from . import puzzle
from . import session
from . import packet
from . import nic


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
            # ignore comments.  Usually coming from the testing files
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
                case "firewall" | "fw":
                    return self.process_firewall(args)
                case "ping":
                    return self.run_ping(args)
                case "replace":
                    return self.replace_something(args)
                case "show" | "list":
                    self.show_info(args)
                case "set":
                    return self.setvalue(args, fromuser)
                case "traceroute" | "tracert":
                    return self.run_traceroute(args)
                case "undo":
                    return self.try_undo()
                case "redo":
                    return self.try_redo()
                case "ups" | "addups":
                    return self.add_ups(args)
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
            session.print("Nothing to undo")

    def try_redo(self):
        if len(session.redolist) > 0:
            lastcmd = session.redolist.pop()
            self.parse(lastcmd.get("forwards"), False, False)
            # The command is automatically added to the undo; through the parse.  We are done
        else:
            session.print("Nothing to redo")

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
                # Make deep clone of the device for our undo
                tcopy = copy.deepcopy(item)

                # go through and clear out all the IP addresses
                for onenic in device.Device(item).all_nics():
                    for oneint in onenic['interface']:
                        if oneint['nicname'] != "lo0":
                            oneint['myip']['ip'] = "0.0.0.0" #reset them all to nothing - the default
                            oneint['myip']['mask'] = "0.0.0.0" #reset them all to nothing - the default

                # clear out the gateway
                item['gateway']['ip'] = "0.0.0.0"
                item['gateway']['mask'] = "0.0.0.0" #this should never be set, but do it just in case

                # remove blownup entry if one exists
                if 'blownup' in item:
                    del item['blownup']

                # mark blowsupwithpower as complete
                session.puzzle.mark_test_as_completed(
                    item.get("hostname"),
                    item.get("hostname"),
                    "DeviceBlowsUpWithPower",
                    f"Successfully replaced {item.get('hostname')}.",
                )

                # Store undo/redo
                session.add_undo_entry(
                    f"delete {item.get('hostname')}",
                    f"restore {item.get('hostname')}",
                    tcopy,
                )

                session.print(f"Successfully replaced {item['hostname']}")
                session.print(f"{item['hostname']} left in an off state")
                #raise NotImplementedError
            else:  # it is something that does not exist
                raise ValueError(f"Not a valid item: {args[0]}")
        if len(args) == 2:
            #We are hopefully finding something like replace pc0 eth0
            item = session.puzzle.device_from_name(args[0])
            if item is not None:
                for onenic in device.Device(item).all_nics():
                    if onenic.get('nicname') == args[1] and onenic['nicname'] != "lo0":
                        #We found the nic to replace.
                        onenic.pop('Mac',None)
                        nic.Nic(onenic).ensure_mac()
                        for oneint in onenic['interface']:
                                oneint['myip']['ip'] = "0.0.0.0" #reset them all to nothing - the default
                                oneint['myip']['mask'] = "0.0.0.0" #reset them all to nothing - the default

            else:  # it is something that does not exist
                raise ValueError(f"Not a valid item: {args[0]}")

    def printhelp(self):
        session.print("--- CLI Help ---")
        session.print(
            "create link source destination - create a link between two devices.  example: create link pc0 net_switch0"
        )
        session.print("delete [item] - delete a device or link")
        session.print(
            "dhcp [item] - have that device do a DHCP or all devices do a DHCP request"
        )
        session.print(
            "firewall device add|del in-interface out-interface drop|allow - Add or remove a firewall rule.  example: firewall pc0 add eth0 eth1 drop"
        )
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
        session.print(
            "traceroute [host1] [host2] - traceroute from one host to the other.  Example: traceroute pc0 pc1"
        )

    def add_ups(self, args):
        if len(args) != 1:
            session.print(
                "Usage: ups [host]"
            )
            session.print(" example: ups pc0")
            return False
        #figure out the host
        shost = session.puzzle.device_from_name(args[0])
        if shost is None:
            shost = session.puzzle.device_from_ip(args[0])
        if shost is None:
            session.print(f"No such host: {args[0]}")
            return False
        session.print(f"Add UPS: {args[0]}")
        #DeviceNeedsUPS
        session.puzzle.mark_test_as_completed(shost['hostname'],shost['hostname'],"DeviceNeedsUPS",f"Added a ups to {shost['hostname']}")

    def run_ping(self, args):
        if len(args) != 2:
            session.print(
                "invalid ping command: usage: ping source_hostname destination_hostname"
            )
            session.print(" example: ping pc0 pc1")
            return False

        # Look for devices by hostname.
        shost = session.puzzle.device_from_name(args[0])
        dhost = session.puzzle.device_from_name(args[1])
        # Look for devices by IP address.
        if shost is None:
            shost = session.puzzle.device_from_ip(args[0])
        if dhost is None:
            dhost = session.puzzle.device_from_ip(args[1])
        if dhost is None and packet.is_ipv4(args[1]):
            dhost = args[1] #it is a valid IP address.  Try it.
        if shost is None:
            session.print(f"No such host: {args[0]}")
            return False
        if dhost is None:
            session.print(f"No such host: {args[1]}")
            return False
        # if we get here, we are ready to try to ping.
        session.print(f"PING: {args[0]} -> {args[1]}")
        device.Ping(shost, dhost)
        # FIXME: This only shows that the ping command was successfully
        # initiated, not that it was itself successful.
        return True

    def run_traceroute(self, args):
        if len(args) != 2:
            session.print(
                "invalid traceroute command: usage: traceroute source_hostname destination_hostname"
            )
            session.print(" example: traceroute pc0 pc1")
            return False

        # Look for devices by hostname.
        shost = session.puzzle.device_from_name(args[0])
        dhost = session.puzzle.device_from_name(args[1])
        # Look for devices by IP address.
        if shost is None:
            shost = session.puzzle.device_from_ip(args[0])
        if dhost is None:
            dhost = session.puzzle.device_from_ip(args[1])
        if shost is None:
            session.print(f"No such host: {args[0]}")
            return False
        if dhost is None:
            session.print(f"No such host: {args[1]}")
            return False
        # if we get here, we are ready to try to ping.
        session.print(f"TRACEROUTE: {args[0]} -> {args[1]}")
        device.Traceroute(shost, dhost)
        # FIXME: This only shows that the ping command was successfully
        # initiated, not that it was itself successful.
        return True


    def do_dhcp(self, args):
        if len(args) == 0:
            # It was simply: dhcp.  We assume 'all'
            args.append("all")
        if args[0] == "all":
            for one in session.puzzle.all_devices():
                if "hostname" in one:
                    device.doDHCP(one.get("hostname"))
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
    
    def process_firewall(self, args):
        if len(args) != 5:
            session.print("invalid firewall command: usage: firewall device add|del in-interface out-interface drop|allow")
            session.print(" example: firewall wrouter0 add eth0:1 eth1 drop")
            session.print(" example: firewall wrouter0 remove eth0:1 eth1 drop")
            return False
        logging.debug(f"parser.Parser.process_firewall({args[0]})")
        target_device = session.puzzle.device_from_name(args[0])
        if target_device is None:
            session.print(f"Cannot process firewall instruction: No such device {args[0]}")
            return False
        d_target_device = device.Device(target_device)
        if not d_target_device.CanDoFirewall:
            session.print(f"invalid device: {args[0]} not allowed to have a firewall")
            return False
        if args[1] not in [ "add", "del", "remove" ]:
            session.print(f"invalid firewall command: {args[1]}  Only add/delete/remove allowed")
            return False
        ininterface = d_target_device.interface_from_name(args[2])
        if ininterface is None:
            session.print(f"invalid interface: {args[2]}")
            return False
        outinterface = d_target_device.interface_from_name(args[3])
        if outinterface is None:
            session.print(f"invalid interface: {args[3]}")
            return False
        if args[4] not in [ "drop", "allow" ]:
            session.print(f"invalid firewall command: {args[4]}  Only allow/drop")
            return False
        #if we get here, we have a valid command.  Determine if we are removing an existing rule, or making a new one
        if args[1] == "add":
            d_target_device.AdvFirewallAdd(args[2],args[3],args[4])
        else:
            d_target_device.AdvFirewallDel(args[2],args[3],args[4])
        

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
                session.print(f"location: {thedevice['location']}")
                if "poweroff" in thedevice and thedevice["poweroff"].lower() == "true":
                    session.print(f"poweroff: {thedevice['poweroff']}")
                if "isdhcp" in thedevice and thedevice["isdhcp"].lower() == "true":
                    session.print(f"DHCP server: {thedevice['isdhcp']}")
                    if thedevice.get('dhcprange') is not None:
                        for item in thedevice.get('dhcprange'):
                            session.print(f"  Range: {item['ip']} {item['mask']}-{item['gateway']}")
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
                    if onetest.get('thetest',"").startswith("Lock"):
                        session.print(f"source: {onetest.get('shost')} test: {onetest.get('thetest')}")
                    else:
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
        if len(args) == 2:
            #hopefully show pc0 eth0 or something like that
            thedevice = session.puzzle.device_from_name(args[0])
            if thedevice is not None:
                #right now, we are hoping it is a hostname and a nic name. Later we may have vlans, etc.
                for onenic in thedevice["nic"]:
                    #print the nic info
                    if(onenic.get('nicname') == args[1]):
                        for oneinterface in onenic.get('interface'):
                            session.print(f"{oneinterface.get('nicname')} - {oneinterface.get('myip').get('ip')}/{oneinterface.get('myip').get('mask')} - {onenic.get('Mac')}")
            else:
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

    def set_dhcp_range(self, dev_obj, value):
        if not device.servesDHCP(dev_obj.json):
            #The device is incapable of being a DHCP server 
            session.print(f"{dev_obj.hostname} is not a dhcp server")
            return False
        if not dev_obj.is_dhcp:
            #The device is capable of being a DHCP server, but that ability is not turned on 
            session.print(f"{dev_obj.hostname} is not a dhcp server")
            return False
        #Now, we need to ensure we have the right settings.
        #   Value should be a range LowIp-HighIp
        #   or Value should be a range ethIP LowIp-HighIp
        #   or Value should be a range ethIP LowIp HighIp
        if len(value) == 0:
            session.print("You must supply a value-range for the DHCP range")
            return False
        startip=""
        endip=""
        ethip=""
        session.print(f"Setting DHCP: {len(value)} items:{value}")
        if len(value) == 1:
            values = value[0].split('-')            
            if len(values) != 2:
                session.print("You must specify a beginning and ending range:  eg. 192.168.1.10-192.168.1.20")
                return False
            startip=values[0]
            endip=values[1]
        if len(value) == 2:
            if ('-' in value[1]):
                #we have an ip,rangestart-rangeend
                values = value[1].split('-')            
                if len(values) != 2:
                    session.print("You must specify a beginning and ending range:  eg. 192.168.1.10-192.168.1.20")
                    return False
                startip=values[0]
                endip=values[1]
                ethip=value[0]
            else:
                #we have a rangestart, rangeend
                startip=value[0]
                endip=value[1]
        if len(value) == 3:
            ethip=value[0]
            startip=value[1]
            endip=value[2]
        ip_list = packet.get_ip_range(startip, endip)
            #If we got here, it worked as a valid IP range.  Accept it.
        if len(ip_list) < 1:
            session.print(f"Invalid DHCP range: {startip} {endip}")
            return False
        #If we get here, it was a valid range.
        #Now we create a new DHCP entry.  It looks like: {ip:[ip of nic], mask:[rangestart],gateway:[range-end],type:"dhcp}
        if ethip == "":
            #We need to figure out the IP address of the ethernet belonging to the range
            localIP = device.sourceIP(dev_obj.json, ipaddress.IPv4Address(startip))
            if localIP is not None and localIP != "":
                ethip =  packet.justIP(localIP)
        if ethip == "":
            session.print("Could not find local IP connected to the ip range specified")
            return False
        #remove the previous record, if one existed
        if dev_obj.json.get('dhcprange') is None:
            dev_obj.json['dhcprange'] = {}
        itemlist = [ record for record in dev_obj.json.get('dhcprange') if record['ip'] != ethip]
        #Now, we create a record and store it.
        newitem = { 
            'ip':ethip,
            'mask':startip,
            'gateway':endip,
            'type':"dhcp"
        }
        itemlist.append(newitem)
        dev_obj.json['dhcprange'] = itemlist
        session.print(f"Setting DHCP range on {dev_obj.hostname} to: {ethip} {startip}-{endip}")

    def set_gateway_value(self, dev_obj, value):
        # we really need to do some type checking.  It should be a valid ipv4 or ipv6 address
        if packet.is_ipv4(value) or packet.is_ipv6(value):
            session.add_undo_entry(
                f"set {dev_obj.hostname} gateway {value}",
                f"set {dev_obj.hostname} gateway {dev_obj.json['gateway']['ip']}",
            )
            dev_obj.json["gateway"]["ip"] = value
            tmp_obj = session.puzzle.device_from_ip(value)
            if tmp_obj is not None and 'hostname' in tmp_obj:
                logging.debug(f"setting {dev_obj.hostname} NeedsDefaultGW to {tmp_obj['hostname']} as solved")
                session.puzzle.mark_test_as_completed(
                        dev_obj.hostname,
                        tmp_obj['hostname'],
                        "NeedsDefaultGW",
                        f"{dev_obj.hostname} has default gateway set",
                    )
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
                if fromuser and nic.get("usesdhcp") == "True":
                    # The user cannot set the IP manually if the NIC is set to use DHCP
                    session.print(
                        f"{nicname} is set for DHCP.  Cannot change it manually."
                    )
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
            #we are trying to turn on the device.
            if session.puzzle.item_blows_up(dev_obj.hostname) or session.puzzle.item_needs_ups(dev_obj.hostname):
                dev_obj.powered_on = True #make sure it is powered off
                dev_obj.blown_up = True
                session.print(f"{dev_obj.hostname} exploded")
                logging.info(f"{dev_obj.hostname} exploded")
                return
            else:
                session.add_undo_entry(
                    f"set {dev_obj.hostname} power on", 
                    f"set {dev_obj.hostname} power {pastvalue}"
                )
                dev_obj.powered_on = False


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
            case "isdhcp":
                self.set_dhcp_value(dev_obj, values[0])
            case "dhcp":
                self.set_dhcp_range(dev_obj, values)
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
                    self.set_ip_value(dev_obj, prop, values[0], fromuser)
