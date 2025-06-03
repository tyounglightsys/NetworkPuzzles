import json
import unittest
from network_puzzles import puzzle
from network_puzzles import session
from network_puzzles import ui
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


class TestXFromY(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = 'Level0-HubVsSwitch'

        # Load puzzle via app in to session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle

        # Load puzzle data separately via json.load.
        puzzle_file = PUZZLES_DIR / f'{self.puzzle_name}.json'
        with puzzle_file.open() as f:
            self.puzzle = json.load(f)  # gets independent puzzle data from file
        self.network = self.puzzle.get('EduNetworkBuilder').get('Network')
        self.device0 = self.network.get('device')[0]  # net_hub0
        self.nic00 = self.device0.get('nic')[0]
        self.device1 = self.network.get('device')[1]  # net_switch0
        self.device4 = self.network.get('device')[4]  # router0
        self.link0 = self.network.get('link')[0]  # link between net_switch0 and router0

    def test_devicefromid_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.device_from_uid('160').get('uniqueidentifier')
        )

    def test_devicefromid_notfound(self):
        self.assertIsNone(session.puzzle.device_from_uid('999'))

    def test_devicefromname_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.device_from_name('net_hub0').get('uniqueidentifier')
        )

    def test_devicefromname_notfound(self):
        self.assertIsNone(session.puzzle.device_from_name('supercool_dev9'))

    def test_itemfromid_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.item_from_uid('160').get('uniqueidentifier')
        )

    def test_itemfromid_notfound(self):
        self.assertIsNone(session.puzzle.item_from_uid('999'))

    def test_linkfromdevices_found(self):
        self.assertEqual(
            self.link0.get('uniqueidentifier'),
            session.puzzle.link_from_devices(self.device1, self.device4).get('uniqueidentifier')
        )

    def test_linkfromdevices_notfound(self):
        self.assertIsNone(session.puzzle.link_from_devices(self.device0, self.device1))

    def test_linkfromid_found(self):
        self.assertEqual(
            self.link0,
            session.puzzle.link_from_uid('146'))

    def test_linkfromid_notfound(self):
        self.assertIsNone(session.puzzle.link_from_uid('999'))

    def test_linkfromname_found(self):
        self.assertEqual(
            self.link0,
            session.puzzle.link_from_name('net_switch0_link_router0'))

    def test_linkfromname_notfound(self):
        self.assertIsNone(session.puzzle.link_from_name('no_such_link'))

    def test_nicfromid_found(self):
        self.assertEqual(
            self.nic00.get('uniqueidentifier'),
            session.puzzle.nic_from_uid('161').get('uniqueidentifier')
        )

    def test_nicfromid_notfound(self):
        self.assertIsNone(session.puzzle.nic_from_uid('999'))