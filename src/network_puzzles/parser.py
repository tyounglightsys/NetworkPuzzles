#This file will be the main parser.  We will pass commands to the puzzle through this.
#Most interaction with the puzzle, making changes or doing actions, will go through this
#import puzzle
import sys
import re
from . import ui
from . import puzzle

def parse(command:str):
    #We will make this a lot more interesting later.  For now, just do a very simple thing
    #try:
        val = None
        cmd = ""
        items = command.split() # break at all whitespace
        if len(items) > 0:
            # we have stuff. Process it
            cmd = items[0].lower()
            match cmd:
                case 'puzzles'|'search':
                    #We want to list all the items.
                    pattern = None
                    if len(items) > 1:
                        pattern = items[1]
                        try:
                            # If it is just a number, look for that level. int(pattern)
                            # throws a ValueError Exception if it fails, so we catch
                            # that specific exception below.
                            pattern = "Level" + str(int(pattern))
                        except ValueError:
                            # otherwise, leave the pattern alone
                            pass
                        if not re.search(r"^\.\*" , pattern):
                            pattern = r".*" + pattern
                        if not re.search(r"\.\*$", pattern):
                            pattern = pattern + r".*"
                    pzs = puzzle.listPuzzles(pattern)
                    val = pzs
                    for a in pzs:
                        print(a)
                    return {'command': cmd, 'value': val}
                case 'load' | 'open':
                    if len(items) == 2:
                        val = puzzle.choosePuzzle(items[1])
                    elif len(items) == 3:
                        val = puzzle.choosePuzzle(items[1], items[2])
                    else:
                        print("loading: ")
                    return {'command':cmd, 'value':val}
                case 'exit' | 'quit' | 'stop':
                     sys.exit()
                case 'ping':
                    if len(items) != 3:
                        print("invalid ping command: usage: ping source_hostname destination_hostname");
                        print(" example: ping pc0 pc1");
                        return None;
                    shost = puzzle.deviceFromName( items[1] );
                    dhost = puzzle.deviceFromName( items[2] );
                    if (shost == None):
                        print("No such host: " + items[1]);
                        return
                    if (dhost == None):
                        print("No such host: " + items[2] );
                        return
                    #if we get here, we are ready to try to ping.
                    puzzle.Ping(shost,dhost);
                case 'show' | 'list':
                    #list the hosts.  Or, show information about a specifici host
                    if len(items) == 1:
                        #Just the show command.  List all the devices
                        devicelist = puzzle.allDevices()
                        for one in devicelist:
                            print(one['hostname'])
                    if len(items) == 2:
                        print ("Not done yet")
                case _:
                    print(f"unknown: {command}")
    #except:
        #We will have a better process later.  Right now, do this simply
        #print("something went wrong parsing.")
