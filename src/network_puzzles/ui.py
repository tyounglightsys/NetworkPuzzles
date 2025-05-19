import sys

from . import current_network
from . import parser
from . import puzzle

class UI:
    TITLE = 'NetworkPuzzles'

    def console_write(self, line):
        """Used to show terminal output to the user."""
        raise NotImplementedError

    def load_puzzle(self, puzzle, filter:str = None):
        """Set up the UI based on the data in the puzzle file.
        Args: 
            puzzle:str - the name of the puzzle itself
            puzzle:int - the index of the puzzle to load
            filter:str - a valid regex filter.  Like ".*DNS.*"  Or None
        """
        val = None
        if filter is not None:
            val=parser.parse("load " + puzzle + " " + filter)
        else:
            val=parser.parse("load " + puzzle)
        
        # Save selected puzzle to current_network.
        current_network.puzzle = val.get('value')
        return val

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
            test=int(what)
            item=puzzle.deviceFromID(what)
        except:
            #if it is not a number, use it as a name
            item=puzzle.deviceFromName(what)
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
            test=int(what)
            item=puzzle.linkFromID(what)
        except:
            #if it is not a number, use it as a name
            item=puzzle.linkFromName(what)
        return item

    def allDevices(self):
        """return a list of all the devices - good for iterating"""
        return puzzle.allDevices()

    def allLinks(self):
        """return a list of all the links - good for iterating"""
        return puzzle.allLinks()



class CLI(UI): 
    def run(self):
        print(self.TITLE)
        self.load_puzzle("5") #for now, just testing
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
        answer = input("-> ")
        parser.parse(answer)

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

    def run(self):
        self.app.run()

    def load_puzzle(self, puzzle, filter:str = None):
        """Load and set up the UI based on the data in the puzzle file."""
        return super().load_puzzle(puzzle,filter).get('value')
        #do any aftermath.  Probably display the loaded puzzle when we have that functionality
