"""Run the GUI App"""

# import os
import sys

# # 1. FORCE KIVY TO USE A DUMMY WINDOW IN HEADLESS ENVIRONMENTS (CI/CD)
# # We check if we are running in GitHub Actions or if the dummy flag is passed
# if "GITHUB_ACTIONS" in os.environ or os.environ.get("KIVY_WINDOW") == "dummy":
#     os.environ["KIVY_NO_ARGS"] = "1"
#     os.environ["KIVY_WINDOW"] = "dummy"
from network_puzzles.gui import NetworkPuzzlesApp
from network_puzzles.ui import GUI

if __name__ == "__main__":
    try:
        app = GUI(kivyapp=NetworkPuzzlesApp)
        app.run()
    except KeyboardInterrupt:
        print()
        sys.exit()
