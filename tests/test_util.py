import unittest

from network_puzzles import ui, util


class TestPuzzleExclusions(unittest.TestCase):
    def setUp(self):
        self.puzzle_names = ui.UI().getAllPuzzleNames()

    def test_exclude_by_level_num(self):
        max_level = 4
        int_names = [i for i in self.puzzle_names if int(i[5]) <= max_level]
        regexp = rf"^Level[{max_level + 1}-9]_.*$"
        filtered_names = util.exclude_from_list(self.puzzle_names, regexp)
        self.assertEqual(int_names, filtered_names)

    def test_exclude_by_pattern(self):
        # Error out if number of puzzles changes.
        self.assertEqual(len(self.puzzle_names), 102)
        regexp = r"^Level(?=[4-9]+|[0-9]+_Help).*$"
        filtered_names = util.exclude_from_list(self.puzzle_names, regexp)
        self.assertEqual(len(filtered_names), 59)
