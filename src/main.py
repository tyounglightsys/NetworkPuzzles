"""Run the GUI App"""

import sys
from network_puzzles.gui import NetworkPuzzlesApp
from network_puzzles.ui import GUI

if __name__ == '__main__':
    try:
        app = GUI(kivyapp=NetworkPuzzlesApp)
        app.run()
    except KeyboardInterrupt:
        print()
        sys.exit()