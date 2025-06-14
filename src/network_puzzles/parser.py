# This file will be the main parser.  We will pass commands to the puzzle through this.
# Most interaction with the puzzle, making changes or doing actions, will go through this
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
            if not pattern.startswith('.*'):
                pattern = r".*" + pattern
            if not pattern.endswith('.*'):
                pattern = pattern + r".*"

        pzs = puzzle.listPuzzles(pattern)
        val = pzs
        for a in pzs:
            session.print(a)
        return {'command': cmd, 'value': val}

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
        return {'command': cmd, 'value': val}

    def parse(self, command: str):
        # We will make this a lot more interesting later.  For now, just do a very simple thing
        items = command.split() # break at all whitespace
        if len(items) > 0:
            # we have stuff. Process it
            cmd = items[0].lower()
            args = items[1:]
            match cmd:
                case 'create':
                    self.create_something(args)
                case 'help'|'?':
                    self.printhelp()
                case 'puzzles' | 'search':
                    return self.get_puzzles(cmd, args)
                case 'load' | 'open':
                    return self.open_puzzle(cmd, args)
                case 'delete':
                    return self.delete_item(args)
                case 'exit' | 'quit' | 'stop':
                    self.exit_app()
                case 'ping':
                    self.run_ping(args)
                case 'show' | 'list':
                    self.show_info(args)
                case 'set':
                    self.setvalue(args)
                case _:
                    session.print(f"unknown: {command}")
        else:
            # If command is empty, do nothing. The prompt will just be reshown.
            pass

    def create_something(self,args):
        if len(args) == 0:
            session.print("You must specify something to print")
            session.print("create link source_hostname [sourcenic] dest_hostname [destnic]")
            session.print("create device devicetype x,y")
            session.print("where devicetype is one of the known devices: pc, laptop, router, switch, firewall, etc.")
            return None
        item = args.pop(0).lower()
        if item == 'link':
            session.puzzle.createLink(args)

    def printhelp(self):
        session.print("--- CLI Help ---")
        session.print("create link source destination - create a link between two devices.  example: create link pc0 net_switch0")
        session.print("delete [item] - delete a device or link")
        session.print("help - show this page")
        session.print("load - load a puzzle.  Example: load 1 | load Level0_Ping")
        session.print("quit - exit the cli")
        session.print("search [info] - list the puzzles matching the info.  Example: search DHCP | search 1")
        session.print("set - change a value.  Example: set pc0 gateway | set pc0 dhcp true")
        session.print("show [item] - show information about an item.  Example: show | show pc0 | show tests")
        session.print("ping [host1] [host2] - ping from one host to the other.  Example: ping pc0 pc1")


    def run_ping(self, args):
        if len(args) != 2:
            session.print("invalid ping command: usage: ping source_hostname destination_hostname")
            session.print(" example: ping pc0 pc1")
            return

        shost = session.puzzle.device_from_name(args[0])
        dhost = session.puzzle.device_from_name(args[1])
        if shost is None:
            session.print(f"No such host: {args[0]}")
            return
        if dhost is None:
            session.print("No such host: " + args[1] )
            return
        # if we get here, we are ready to try to ping.
        session.print(f"PING {args[1]} from {args[0]}")
        device.Ping(shost, dhost)
    
    def delete_item(self, args):
        if len(args) == 0:
            session.print("invalid delete command: usage: delete item")
            session.print(" example: delete pc0")
            session.print(" example: delete pc0_link_net_switch0")
            return False
        target_device = session.puzzle.device_from_name(args[0])
        if target_device is None:
            target_device = session.puzzle.link_from_name(args[0])
        if target_device is None:
            session.print(f"Cannot delete: No such item {args[0]}")
            return False
        #check to see if we are able to delete.  Is it locked?
        #We will need to check for that later after the tests are done.
        session.print(f"Deleting {args[0]}")
        session.puzzle.deleteItem(args[0])

    def show_info(self, args):
        # list the hosts.  Or, show information about a specifici host
        if len(args) == 0:
            # Just the show command.  List all the devices
            session.print(session.puzzle.json.get('name'))
            devicelist = session.puzzle.all_devices()
            if len(devicelist) > 0:
                session.print("----devices----")
            for one in devicelist:
                session.print(one['hostname'])
            linklist=session.puzzle.all_links()
            if len(linklist) > 0:
                session.print("----links----")
            for one in linklist:
                session.print(one['hostname'])
        if len(args) == 1:
            thedevice = session.puzzle.device_from_name(args[0])
            if thedevice is not None:
                #we have a valid device.  Show information about the device
                session.print("----Device----")
                session.print(f"hostname: {thedevice['hostname']}")
                if 'poweroff' in thedevice and thedevice['poweroff'].lower() == 'true':
                    session.print(f"poweroff: {thedevice['poweroff']}")
                if 'isdhcp' in thedevice and thedevice['isdhcp'].lower() == 'true':
                    session.print(f"DHCP server: {thedevice['isdhcp']}")
                session.print(f"gateway: {thedevice['gateway']['ip']}")
                for onestring in device.allIPStrings(thedevice,True,True):
                    session.print(onestring)
                return
            thedevice = session.puzzle.link_from_name(args[0])
            if thedevice is not None:
                #we have a valid link.  Show information about the link
                session.print("----Link----")
                session.print(f"name: {thedevice['hostname']}")
                session.print(f"type: {thedevice['linktype']}")
                session.print(f"source: {thedevice['SrcNic']['hostname']} - {thedevice['SrcNic']['nicname']}")
                session.print(f"dest: {thedevice['DstNic']['hostname']} - {thedevice['DstNic']['nicname']}")
                return
            if args[0].lower() == 'tests':
                session.print("--Tests--")
                for onetest in device.all_tests():
                    session.print(f"source: {onetest.get('shost')} test: {onetest.get('thetest')}  dest: {onetest.get('dhost')} status: {onetest.get('completed','False')}")
                return
            if args[0].lower() == 'puzzle':
                session.print("----Puzzle----")
                session.print(session.puzzle.json.get('name'))
                session.print(session.puzzle.json.get('en_title'))
                session.print(session.puzzle.json.get('en_message'))
                self.show_info([])
                self.show_info(["tests"])
                return
            session.print(f"No such host {args[0]}")



    def setvalue(self,args):
        #set a value on a device.
        #right now, we have something like: set pc0 poweroff true
        if len(args) == 3:
            chosendevice = session.puzzle.device_from_name(args[0])
            if chosendevice is not None:
                match args[1].lower():
                    case 'power'|'poweroff':
                        if args[2].lower() == "off":
                            chosendevice['poweroff'] = 'True'
                        else:
                            chosendevice['poweroff']= 'False'
                        session.print(f"Defining {args[0]} 'poweroff' to {chosendevice['poweroff']}")
                    case 'dhcp'|'isdhcp':
                        if args[2].lower() == "yes":
                            chosendevice['isdhcp'] = 'True'
                        else:
                            chosendevice['isdhcp']= 'False'
                        session.print(f"Defining {args[0]} 'isdhcp' to {chosendevice['isdhcp']}")
                    case 'gateway'|'gw':
                        #we really need to do some type checking.  It should be a valid ipv4 or ipv6 address
                        if packet.is_ipv4(args[2]) or packet.is_ipv6(args[2]):
                            chosendevice['gateway']['ip']= args[2]
                            session.print(f"Setting {args[0]} gateway: {chosendevice['gateway']['ip']}")
                        else:
                            session.print(f"invalid address: {args[2]}")
