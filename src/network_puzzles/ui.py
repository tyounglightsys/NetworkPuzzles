import sys

from . import device
from . import parser
from . import puzzle
from . import session
from . import packet

class UI:
    TITLE = 'NetworkPuzzles'

    def console_write(self, line):
        """Used to show terminal output to the user."""
        raise NotImplementedError

    def load_puzzle(self, puzzle_ref, filter:str = None):
        """Set up the UI based on the data in the puzzle file.
        Args: 
            puzzle:str - the name of the puzzle itself
            puzzle:int - the index of the puzzle to load
            filter:str - a valid regex filter.  Like ".*DNS.*"  Or None
        """
        val = None
        if filter is not None:
            val=parser.parse("load " + puzzle_ref + " " + filter)
        else:
            val=parser.parse("load " + puzzle_ref)
        
        # Save selected puzzle to session variable.
        session.puzzle = val.get('value')
        session.puzzle_obj = puzzle.Puzzle(val.get('value'))
        return val

    def quit(self):
        raise NotImplementedError

    def run(self):
        """Startup the app when first launched."""
        raise NotImplementedError

    def getAllPuzzleNames(self,filter=None):
        """return a list of all the puzzle names
        Args: filter:str a string, regex filter such as '.*DHCP.'"""
        return puzzle.listPuzzles(filter)

    def getDevice(self,what:str):
        """Return a device from either a name or ID
        Args: what:str - a string value that is either a hostname 'pc0' or a device id '102'
        Returns: a device record or None
        """
        #try retrieving it from name
        item=None
        try:
            #if it is just a number, use it as an ID
            int(what)
            item=device.deviceFromID(what)
        except ValueError:
            #if it is not a number, use it as a name
            item=device.deviceFromName(what)
        return item


    def getLink(self,what:str):
        """Return a link from either a name or ID
        Args: what:str - a string value that is either a linkname 'pc0_link_pc1' or a device id '102'
        Returns: a device record or None
        """
        #try retrieving it from name
        item=None
        try:
            #if it is just a number, use it as an ID
            int(what)
            item=device.linkFromID(what)
        except ValueError:
            #if it is not a number, use it as a name
            item=device.linkFromName(what)
        return item

    def allDevices(self):
        """return a list of all the devices - good for iterating"""
        return device.allDevices()

    def allLinks(self):
        """return a list of all the links - good for iterating"""
        return device.allLinks()



class CLI(UI): 
    def run(self):
        print(self.TITLE)
        self.load_puzzle("2") #for now, just testing
        try:
            while True:
                self.prompt()
        except KeyboardInterrupt:
            print()
            sys.exit()

    def console_write(self,message):
        """How the GUI handles messages"""
        print(message)

    def prompt(self):
        """A CLI only function.  Prompt for imput and process it"""
        try:
            answer = input("-> ")
            parser.parse(answer)
            #if we created packets, process them until done.
            while packet.packetsNeedProcessing():
                packet.processPackets(2) #the cli does not need much time to know packets are going to loop forever.
        except EOFError:
            sys.exit()

    def quit(self):
        parser.exit_app()

    def load_puzzle(self, puzzle, filter:str = None):
        """Load and set up the UI based on the data in the puzzle file."""
        super().load_puzzle(puzzle,filter)
        #do any aftermath.  Probably display the loaded puzzle when we have that functionality

class GUI(UI):
    def __init__(self, kivyapp):
        self.app = kivyapp(ui=self)
        # self.app.title = self.TITLE  # inferred from App subclass in .gui

    def console_write(self, line):
        self.app.add_terminal_line(line)

    def load_puzzle(self, puzzle, filter:str = None):
        """Load and set up the UI based on the data in the puzzle file."""
        return super().load_puzzle(puzzle,filter).get('value')
        #do any aftermath.  Probably display the loaded puzzle when we have that functionality

    def parse(self, command: str):
        parser.parse(command)

    def process_packets(self, delay):
        # if we created packets, process them until done.
        if packet.packetsNeedProcessing():
            packet.processPackets(2, tick_pct=100*delay)

    def quit(self):
        self.app.stop()

    def run(self):
        self.app.run()
