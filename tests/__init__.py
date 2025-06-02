import sys
from pathlib import Path

# Add package dir to PYTHONPATH.
sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))

PUZZLES_DIR = puzzle_file = Path(__file__).parents[1] / 'src' / 'network_puzzles' / 'resources' / 'puzzles'