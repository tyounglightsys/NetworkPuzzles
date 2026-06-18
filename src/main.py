"""Run the GUI App"""

# import os
import sys

# Force Kivy to use the dummy renderer in headless environments (like CI/CD runners)
# if "GITHUB_ACTIONS" in os.environ:
#     os.environ["KIVY_WINDOW"] = "dummy"
#     os.environ["KIVY_GL_BACKEND"] = "dummy"
from network_puzzles.gui import NetworkPuzzlesApp
from network_puzzles.ui import GUI

if __name__ == "__main__":
    try:
        app = GUI(kivyapp=NetworkPuzzlesApp)
        app.run()
    except KeyboardInterrupt:
        print()
        sys.exit()
