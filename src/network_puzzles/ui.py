import logging
import sys

from . import packet, parser, puzzle, session


class UI:
    TITLE = "NetworkPuzzles"
    PS1 = "->"

    def __init__(self):
        self.parser = parser.Parser()
        session.ui = self

    @property
    def puzzle(self):
        """Convenience attribute."""
        return session.puzzle

    def acknowledge_any_tests(self):
        for test_data in self.puzzle.tests:
            test = puzzle.PuzzleTest(test_data)
            if (
                test.name == "SuccessfullyPingsWithoutLoop"
                and session.packetstorm
                and not test.acknowledged
            ):
                test.completed = False
            if test.completed and not test.acknowledged:
                # we have something completed, but not acknowledged
                if test.message:
                    session.print(test.message)
                test.acknowledged = True

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

    def notify_if_puzzle_completed(self):
        if self.puzzle.is_solved():
            session.print("Congratulations. You solved the whole puzzle!")
            self.puzzle.completion_notified = True

    def quit(self):
        raise NotImplementedError

    def run(self):
        """Startup the app when first launched."""
        raise NotImplementedError

    def update_puzzle_completion_status(self):
        if self.puzzle and not self.puzzle.completion_notified:
            self.acknowledge_any_tests()
            self.notify_if_puzzle_completed()
            if self.puzzle.is_solved():
                self.parser.parse("show tests", False)
            return self.puzzle.is_solved()

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
            item = self.puzzle.device_from_uid(what)
        except ValueError:
            # if it is not a number, use it as a name
            item = self.puzzle.device_from_name(what)
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
            item = self.puzzle.link_from_uid(what)
        except ValueError:
            # if it is not a number, use it as a name
            item = self.puzzle.link_from_name(what)
        return item

    def all_devices(self):
        """return a list of all the devices - good for iterating"""
        return [d for d in self.puzzle.devices]

    def all_links(self):
        """return a list of all the links - good for iterating"""
        return [k for k in self.puzzle.links]

    def all_tests(self):
        """return a list of all tests in the current puzzle"""
        return self.puzzle.all_tests()

    def redraw(self):
        pass

    def redo(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class CLI(UI):
    def __init__(self):
        self.parser = parser.Parser()
        session.print = self.console_write
        session.ui = self

    def run(self):
        print(self.TITLE)
        what = "2"  # for now, just testing
        if session.startinglevel != "":
            what = session.startinglevel
        self.load_puzzle(what)  # for now, just testing
        try:
            while True:
                self.prompt()
        except KeyboardInterrupt:
            print()
            sys.exit()

    def console_write(self, message):
        """How the GUI handles messages"""
        print(message)

    def process_packets(self):
        # if we created packets, process them until done.
        count = 0
        while session.puzzle.packets_need_processing():
            count = count + 1
            if count > 5:
                self.acknowledge_any_tests()
                count = 0
            # The cli does not need much time to know packets are going to
            # loop forever.
            session.puzzle.process_packets(2)

    def prompt(self):
        """A CLI only function.  Prompt for imput and process it"""
        try:
            answer = input(f"{self.PS1} ")
            self.parser.parse(answer, True)
            # If we created packets, process them until done.
            self.process_packets()
            # Check if puzzle is complete.
            self.update_puzzle_completion_status()
        except EOFError:
            sys.exit()

    def quit(self):
        self.parser.parse.exit_app()


class GUI(UI):
    def __init__(self, kivyapp):
        self.app = kivyapp(ui=self)
        self.parser = parser.Parser()
        session.print = self.console_write
        session.ui = self

    def console_write(self, line):
        self.app.add_terminal_line(line)
        logging.info(f"GUI: terminal: {line}")

    def parse(self, command: str):
        self.parser.parse(command)
        # Update GUI after every command.
        # NOTE: Any asynchronous commands (e.g. ping) will need their own forced
        # redraws at the end of the command.
        self.redraw()

    def process_packets(self, tick_pct):
        # If we created packets, process them until done.
        if self.puzzle.packets_need_processing():
            session.puzzle.process_packets(tick_pct=tick_pct)

    def quit(self):
        self.app.stop()

    def redo(self):
        self.parse("redo")

    def redraw(self):
        self.app.draw_puzzle()
        self.app.check_puzzle()
        self.app.update_help()
        self.app.update_undo_redo_states()

    def run(self):
        self.app.run()

    def undo(self):
        self.parse("undo")
