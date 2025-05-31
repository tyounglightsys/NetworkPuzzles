# This file will be the main parser.  We will pass commands to the puzzle through this.
# Most interaction with the puzzle, making changes or doing actions, will go through this
import sys
from . import puzzle
from . import session


def parse(command:str):
    # We will make this a lot more interesting later.  For now, just do a very simple thing
    items = command.split() # break at all whitespace
    if len(items) > 0:
        # we have stuff. Process it
        cmd = items[0].lower()
        args = items[1:]
        match cmd:
            case 'puzzles' | 'search':
                return get_puzzles(cmd, args)
            case 'load' | 'open':
                return open_puzzle(cmd, args)
            case 'exit' | 'quit' | 'stop':
                exit_app()
            case 'ping':
                run_ping(args)
            case 'show' | 'list':
                show_info(args)
            case _:
                print(f"unknown: {command}")
    else:
        # If command is empty, do nothing. The prompt will just be reshown.
        pass


def exit_app():
    sys.exit()


def get_puzzles(cmd, args):
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
        print(a)
    return {'command': cmd, 'value': val}


def open_puzzle(cmd, args):
    val = None
    if len(args) == 1:
        val = puzzle.choosePuzzle(args[0])
    elif len(args) == 2:
        val = puzzle.choosePuzzle(args[0], args[1])
    else:
        print("loading: ")
    return {'command': cmd, 'value': val}


def run_ping(args):
    if len(args) != 2:
        print("invalid ping command: usage: ping source_hostname destination_hostname")
        print(" example: ping pc0 pc1")
        return
    shost = puzzle.deviceFromName(args[0])
    dhost = puzzle.deviceFromName(args[1])
    if shost is None:
        print(f"No such host: {args[0]}")
        return
    if dhost is None:
        print("No such host: " + args[1] )
        return
    # if we get here, we are ready to try to ping.
    puzzle.Ping(shost, dhost)


def show_info(args):
    # list the hosts.  Or, show information about a specifici host
    if len(args) == 0:
        # Just the show command.  List all the devices
        print (session.puzzle['name'])
        devicelist = puzzle.allDevices()
        for one in devicelist:
            print(one['hostname'])
    if len(args) == 1:
        print ("Not done yet")