"""Run the GUI App"""

# import os
import sys

# from kivy.resources import resource_add_path
# if __name__ == "__main__":
#     if hasattr(sys, "_MEIPASS"):
#         resource_add_path(os.path.join(sys._MEIPASS))
from network_puzzles.gui import NetworkPuzzlesApp
from network_puzzles.ui import GUI

if __name__ == "__main__":
    try:
        app = GUI(kivyapp=NetworkPuzzlesApp)
        app.run()
    except KeyboardInterrupt:
        print()
        sys.exit()
