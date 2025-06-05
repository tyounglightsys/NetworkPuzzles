# This file will be the main parser.  We will pass commands to the puzzle through this.
# Most interaction with the puzzle, making changes or doing actions, will go through this
import sys
from . import device
from . import puzzle
from . import session
from . import packet


class Parser:
    def __init__(self, ui=None):
        self.ui = ui
        if self.ui is None:
            self.print = print
        else:
            self.print = self.ui.console_write

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
            self.print(a)
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
            self.print("loading: ")
        return {'command': cmd, 'value': val}

    def parse(self, command: str):
        # We will make this a lot more interesting later.  For now, just do a very simple thing
        items = command.split() # break at all whitespace
        if len(items) > 0:
            # we have stuff. Process it
            cmd = items[0].lower()
            args = items[1:]
            match cmd:
                case 'puzzles' | 'search':
                    return self.get_puzzles(cmd, args)
                case 'load' | 'open':
                    return self.open_puzzle(cmd, args)
                case 'exit' | 'quit' | 'stop':
                    self.exit_app()
                case 'ping':
                    self.run_ping(args)
                case 'show' | 'list':
                    self.show_info(args)
                case 'set':
                    self.setvalue(args)
                case _:
                    self.print(f"unknown: {command}")
        else:
            # If command is empty, do nothing. The prompt will just be reshown.
            pass

    def run_ping(self, args):
        if len(args) != 2:
            self.print("invalid ping command: usage: ping source_hostname destination_hostname")
            self.print(" example: ping pc0 pc1")
            return

        shost = session.puzzle.device_from_name(args[0])
        dhost = session.puzzle.device_from_name(args[1])
        if shost is None:
            self.print(f"No such host: {args[0]}")
            return
        if dhost is None:
            self.print("No such host: " + args[1] )
            return
        # if we get here, we are ready to try to ping.
        self.print(f"PING {args[1]} from {args[0]}")
        device.Ping(shost, dhost)
    
    def show_info(self, args):
        # list the hosts.  Or, show information about a specifici host
        if len(args) == 0:
            # Just the show command.  List all the devices
            self.print(session.puzzle.json.get('name'))
            devicelist = session.puzzle.all_devices()
            if len(devicelist) > 0:
                self.print("----devices----")
            for one in devicelist:
                self.print(one['hostname'])
            linklist=session.puzzle.all_links()
            if len(linklist) > 0:
                self.print("----links----")
            for one in linklist:
                self.print(one['hostname'])
        if len(args) == 1:
            thedevice = session.puzzle.device_from_name(args[0])
            if thedevice is not None:
                #we have a valid device.  Show information about the device
                self.print("----Device----")
                self.print(f"hostname: {thedevice['hostname']}")
                if 'poweroff' in thedevice and thedevice['poweroff'].lower() == 'true':
                    self.print(f"poweroff: {thedevice['poweroff']}")
                self.print(f"gateway: {thedevice['gateway']['ip']}")
                for onestring in device.allIPStrings(thedevice,True,True):
                    self.print(onestring)
                return
            thedevice = session.puzzle.link_from_name(args[0])
            if thedevice is not None:
                #we have a valid link.  Show information about the link
                self.print("----Link----")
                self.print(f"name: {thedevice['hostname']}")
                self.print(f"type: {thedevice['linktype']}")
                self.print(f"source: {thedevice['SrcNic']['hostname']} - {thedevice['SrcNic']['nicname']}")
                self.print(f"dest: {thedevice['DstNic']['hostname']} - {thedevice['DstNic']['nicname']}")
                return
            self.print(f"No such host {args[0]}")



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
                        self.print(f"Defining {args[0]} 'poweroff' to {chosendevice['poweroff']}")
                    case 'dhcp'|'isdhcp':
                        if args[2].lower() == "yes":
                            chosendevice['isdhcp'] = 'True'
                        else:
                            chosendevice['isdhcp']= 'False'
                        self.print(f"Defining {args[0]} 'isdhcp' to {chosendevice['isdhcp']}")
                    case 'gateway'|'gw':
                        #we really need to do some type checking.  It should be a valid ipv4 or ipv6 address
                        if packet.is_ipv4(args[2]) or packet.is_ipv6(args[2]):
                            chosendevice['gateway']['ip']= args[2]
                            self.print(f"Setting {args[0]} gateway: {chosendevice['gateway']['ip']}")
                        else:
                            self.print(f"invalid address: {args[2]}")
