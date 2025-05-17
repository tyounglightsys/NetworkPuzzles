#This file will be the main parser.  We will pass commands to the puzzle through this.
#Most interaction with the puzzle, making changes or doing actions, will go through this
#import puzzle
import sys
import re
from src.network_puzzles import ui
from src.network_puzzles import puzzle

def parse(command:str):
    #We will make this a lot more interesting later.  For now, just do a very simple thing
    #try:
        items = command.split() #break at all whitespace
        if len(items) > 0:
            #we have stuff.  Process it
            if items[0].lower() in ['list','show','search']:
                #We want to list all the items.
                pattern=None
                if(len(items) > 1):
                    pattern=items[1]
                    try:
                        #If it is just a number, look for that level
                        pattern="Level"+str(int(pattern))
                    except:
                        #otherwise, leave the pattern alone
                        pattern=pattern
                    if not re.search(r"^\.\*",pattern):
                        pattern=r".*"+pattern
                    if not re.search(r"\.\*$",pattern):
                        pattern=pattern+r".*"
                list=puzzle.listPuzzles(pattern)
                for a in list:
                     print(a)
            elif items[0].lower() in ['load', 'open']:
                if len(items) == 2:
                    puzzle.choosePuzzle(items[1])
                elif len(items) == 3:
                    puzzle.choosePuzzle(items[1],items[2])

                else:
                    print("loading: ")
            elif items[0].lower() in ['exit', 'quit', 'stop']:
                 sys.exit()
            else:
                print("unknown: " + command)
    #except:
        #We will have a better process later.  Right now, do this simply
        #print("something went wrong parsing.")
