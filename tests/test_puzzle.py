import unittest
from network_puzzles import puzzle
from . import PUZZLES_DIR


class TestMatchesFilter(unittest.TestCase):
    def test_match(self):
        self.assertTrue(puzzle.matches_filter('crazylongname', r'.*name.*'))

    def test_matchothercase(self):
        self.assertTrue(puzzle.matches_filter('CrazyLongName', r'.*name.*'))

    def test_nofilter(self):
        self.assertTrue(puzzle.matches_filter('test', None))

    def test_nomatch(self):
        self.assertFalse(puzzle.matches_filter('crazylongname', r'.*dhcp.*'))


class TestFilterItems(unittest.TestCase):
    def setUp(self):
        self.puzzles = [
            {
                'EduNetworkBuilder': {
                    'Network': {
                        'name': 'puzzle1_dhcp'
                    }
                }
            },
            {
                'EduNetworkBuilder': {
                    'Network': {
                        'name': 'puzzle2_vlan'
                    }
                }
            },
        ]
        self.puzzle_names = [
            'puzzle1_dhcp',
            'puzzle2_vlan',
        ]
        self.puzzle_files = [str(f).replace('.json', '') for f in PUZZLES_DIR.glob('*.json')]

    def test_disk_filter(self):
        dhcp_files = [f for f in self.puzzle_files if 'dhcp' in f.lower()]
        self.assertEqual(dhcp_files, puzzle.filter_items(self.puzzle_files, '.*DHCP.*', json_files=True))

    def test_dist_nofilter(self):
        
        self.assertEqual(sorted(self.puzzle_files), sorted(puzzle.filter_items(self.puzzle_files, None, json_files=True)))

    def test_memory_filter(self):
        self.assertEqual(self.puzzle_names[:1], puzzle.filter_items(self.puzzles, '.*DHCP.*'))

    def test_memory_nofilter(self):
        self.assertEqual(self.puzzle_names, puzzle.filter_items(self.puzzles, None))

