import sys
from pathlib import Path

# Add package dir to PYTHONPATH.
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

# Empty out unittest args to avoid interference with argparse.
if sys.argv[0].endswith("unittest"):
    sys.argv = sys.argv[:1]

PUZZLES_DIR = puzzle_file = (
    Path(__file__).parents[1] / "src" / "network_puzzles" / "resources" / "puzzles"
)
