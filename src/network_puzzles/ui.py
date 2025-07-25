import sys

from . import parser
from . import puzzle
from . import session
from . import packet


class UI:
    TITLE = "NetworkPuzzles"

    def __init__(self):
        self.parser = parser.Parser()
        session.ui = self

    @property
    def packetlist(self):
        return session.packetlist

    @property
    def puzzle(self):
        return session.puzzle

    def console_write(self, line):
        """Used to show terminal output to the user."""
        raise NotImplementedError

    def load_puzzle(self, puzzle_ref, filter: str = None):
        """Set up the UI based on the data in the puzzle file.
        Args:
            puzzle:str - the name of the puzzle itself
            puzzle:int - the index of the puzzle to load
            filter:str - a valid regex filter.  Like ".*DNS.*"  Or None
        """
        val = None
        if filter is not None:
            val = self.parser.parse("load " + puzzle_ref + " " + filter, False)
        else:
            val = self.parser.parse("load " + puzzle_ref, False)

        # Save selected puzzle to session variable.
        session.puzzle = puzzle.Puzzle(val.get("value"))

    def quit(self):
        raise NotImplementedError

    def run(self):
        """Startup the app when first launched."""
        raise NotImplementedError

    def getAllPuzzleNames(self, filter=None):
        """return a list of all the puzzle names
        Args: filter:str a string, regex filter such as '.*DHCP.'"""
        return puzzle.listPuzzles(filter)

    def get_device(self, what: str) -> dict | None:
        """Return a device from either a name or ID
        Args: what:str - a string value that is either a hostname 'pc0' or a device id '102'
        Returns: a device record or None
        """
        # try retrieving it from name
        item = None
        try:
            # if it is just a number, use it as an ID
            int(what)
            item = session.puzzle.device_from_uid(what)
        except ValueError:
            # if it is not a number, use it as a name
            item = session.puzzle.device_from_name(what)
        return item

    def get_link(self, what: str) -> dict | None:
        """Return a link from either a name or ID
        Args: what:str - a string value that is either a linkname 'pc0_link_pc1' or a device id '102'
        Returns: a device record or None
        """
        # try retrieving it from name
        item = None
        try:
            # if it is just a number, use it as an ID
            int(what)
            item = session.puzzle.link_from_uid(what)
        except ValueError:
            # if it is not a number, use it as a name
            item = session.puzzle.link_from_name(what)
        return item

    def all_devices(self):
        """return a list of all the devices - good for iterating"""
        return [d for d in session.puzzle.devices]

    def all_links(self):
        """return a list of all the links - good for iterating"""
        return [k for k in session.puzzle.links]

    def all_tests(self):
        """return a list of all tests in the current puzzle"""
        return session.puzzle.all_tests()

    def create_link(self, *args):
        pass

    def delete_item(self, *args):
        pass

    def replace_link(self, *args):
        pass

    def update_power_status(self, *args):
        pass

    def acknowledge_any_tests():
        raise NotImplementedError


class CLI(UI):
    def __init__(self):
        self.parser = parser.Parser()
        session.print = self.console_write
        session.ui = self

    def run(self):
        print(self.TITLE)
        self.load_puzzle("2")  # for now, just testing
        try:
            while True:
                self.prompt()
        except KeyboardInterrupt:
            print()
            sys.exit()

    def console_write(self, message):
        """How the GUI handles messages"""
        print(message)

    def prompt(self):
        """A CLI only function.  Prompt for imput and process it"""
        try:
            answer = input("-> ")
            self.parser.parse(answer, True)
            # if we created packets, process them until done.
            count = 0
            while packet.packetsNeedProcessing():
                count = count + 1
                if count > 5:
                    self.acknowledge_any_tests()
                    count = 0
                packet.processPackets(
                    2
                )  # the cli does not need much time to know packets are going to loop forever.
            self.acknowledge_any_tests()
            if not session.puzzle.json.get("completed", False):
                if session.puzzle.is_puzzle_done():
                    session.print("Congratulations. You solved the whole puzzle!")
                    self.parser.parse("show tests", False)
                    session.puzzle.json["completed"] = True
        except EOFError:
            sys.exit()

    def acknowledge_any_tests(self):
        for test in session.puzzle.all_tests():
            if (
                test.get("thetest", "") == "SuccessfullyPingsWithoutLoop"
                and session.packetstorm
                and not test.get("acknowledged", False)
            ):
                # The ping was successful, but the storm did happen.  Mark it as false
                test["completed"] = False
            if test.get("completed", False) and not test.get("acknowledged", False):
                # we have something completed, but not acknowledged
                if test.get("message", "") != "":
                    session.print(test.get("message", ""))
                    test["acknowledged"] = True

    def quit(self):
        self.parser.parse.exit_app()

    def load_puzzle(self, puzzle, filter_str: str = None):
        """Load and set up the UI based on the data in the puzzle file."""
        super().load_puzzle(puzzle, filter_str)
        # do any aftermath.  Probably display the loaded puzzle when we have that functionality


class GUI(UI):
    def __init__(self, kivyapp):
        self.app = kivyapp(ui=self)
        self.parser = parser.Parser()
        session.print = self.console_write
        session.ui = self

    def acknowledge_any_tests(self):
        for test in session.puzzle.all_tests():
            if (
                test.get("thetest", "") == "SuccessfullyPingsWithoutLoop"
                and session.packetstorm
                and not test.get("acknowledged", False)
            ):
                # The ping was successful, but the storm did happen.  Mark it as false
                test["completed"] = False
            if test.get("completed", False) and not test.get("acknowledged", False):
                # we have something completed, but not acknowledged
                if test.get("message") is not None:
                    session.print(test.get("message", ""))
                    test["acknowledged"] = True

    def console_write(self, line):
        self.app.add_terminal_line(line)

    def create_link(self, link_data):
        self.app.add_link(link_data)

    def delete_item(self, item_data):
        self.app.remove_item(item_data)

    def is_puzzle_done(self, *args) -> bool | None:
        """
        Determine if puzzle has been solved.

        Return None if no puzzle is active, or True|False according to active
        puzzle's solved state.
        """
        if self.puzzle:
            # First check if completed tests have been acknowledged.
            self.acknowledge_any_tests()
            # Check if puzzle is complete.
            if not session.puzzle.json.get("completed"):
                if session.puzzle.is_puzzle_done():
                    session.print("Congratulations. You solved the whole puzzle!")
                    # self.parser.parse("show tests", False)
                    session.puzzle.json["completed"] = True
                    return True
                else:
                    return False
        else:
            return None

    def parse(self, command: str):
        self.parser.parse(command)

    def process_packets(self, tick_pct):
        # If we created packets, process them until done.
        if packet.packetsNeedProcessing():
            packet.processPackets(4, tick_pct=tick_pct)

    def quit(self):
        self.app.stop()

    def replace_link(self, link_data):
        self.delete_item(link_data)
        self.create_link(link_data)

    def run(self):
        self.app.run()

    def update_power_status(self, hostname):
        device = self.app.get_widget_by_hostname(hostname)
        if device:
            device.set_power_status()
