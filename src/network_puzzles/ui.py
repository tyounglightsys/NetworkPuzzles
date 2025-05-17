from src.network_puzzles import parser
from src.network_puzzles import puzzle
import sys

class UI:
    TITLE = 'NetworkPuzzles'

    def console_write(self, line):
        """Used to show terminal output to the user."""
        raise NotImplementedError

    def load_puzzle(self, puzzle, filter:str=None):
        """Set up the UI based on the data in the puzzle file.
        Args: 
            puzzle:str - the name of the puzzle itself
            puzzle:int - the index of the puzzle to load
            filter:str - a valid regex filter.  Like ".*DNS.*"  Or None
        """
        if filter != None:
            parser.parse("load " + puzzle + " " + filter)
        else:
            parser.parse("load " + puzzle)

    def run(self):
        """Startup the app when first launched."""
        raise NotImplementedError


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
        self.app = kivyapp()
        # self.app.title = self.TITLE  # inferred from App subclass in .gui

    def run(self):
        self.app.run()

    def load_puzzle(self, puzzle, filter:str = None):
        """Load and set up the UI based on the data in the puzzle file."""
        super().load_puzzle(puzzle,filter)
        #do any aftermath.  Probably display the loaded puzzle when we have that functionality
