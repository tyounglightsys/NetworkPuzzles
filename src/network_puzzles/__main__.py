"""Run the CLI App"""

import sys

from network_puzzles.ui import CLI

if __name__ == '__main__':
    try:
        app = CLI()
        app.run()
    except KeyboardInterrupt:
        print()
        sys.exit()
