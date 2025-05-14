"""Run the CLI App"""

import sys
from .ui import CLI


if __name__ == '__main__':
    try:
        app = CLI()
        app.run()
    except KeyboardInterrupt:
        print()
        sys.exit()