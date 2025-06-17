import json
import re
import unittest
from network_puzzles import puzzle
from network_puzzles import session
from network_puzzles import ui
from . import PUZZLES_DIR


class TestCreateItems(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = 'Level0_NeedsLink'

        # Load puzzle via app into session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle

    def test_createlink_exists(self):
        # FIXME: The method always returns None. The only way to verify
        # correct execution for an error situation is to check the stdout.
        self.assertIsNone(session.puzzle.createLink(['pc1', 'net_switch0']))

    def test_createlink_good(self):
        prev_ct = len(session.puzzle.all_links())
        session.puzzle.createLink(['pc0', 'net_switch0'])
        ct = len(session.puzzle.all_links())
        self.assertEqual(prev_ct + 1, ct)

    def test_createlink_noargs(self):
        # FIXME: The method always returns None. The only way to verify
        # correct execution for an error situation is to check the stdout.
        self.assertIsNone(session.puzzle.createLink([]))


class TestListItemsJson(unittest.TestCase):
    """Ensure items found match items in original JSON file."""
    def setUp(self):
        self.puzzle_name = 'Level0_HubVsSwitch'

        # Load puzzle via app in to session.puzzle.
        ui.CLI().load_puzzle(self.puzzle_name)  # sets session.puzzle

        # Load puzzle data separately via json.load.
        puzzle_file = PUZZLES_DIR / f'{self.puzzle_name}.json'
        with puzzle_file.open() as f:
            self.puzzle = json.load(f)  # gets independent puzzle data from file
        self.network = self.puzzle.get('EduNetworkBuilder').get('Network')

    def test_alldevices(self):
        devices = self.network.get('device')
        self.assertEqual(len(devices), len(session.puzzle.all_devices()))

    def test_alllinks(self):
        links = self.network.get('link')
        self.assertEqual(len(links), len(session.puzzle.all_links()))

    def test_alltests(self):
        tests = self.network.get('nettest')
        self.assertEqual(len(tests), len(session.puzzle.all_tests()))

    def test_deviceiscritical_false(self):
        self.assertFalse(session.puzzle.device_is_critical('net_hub0'))

    def test_deviceiscritical_true(self):
        test_devices = set()
        for test in self.network.get('nettest'):
            for host in ('shost', 'dhost'):
                hostname = test.get(host)
                if hostname:
                    test_devices.add(hostname)
        for d in test_devices:
            self.assertTrue(session.puzzle.device_is_critical(d))


class TestListItemsTypes(unittest.TestCase):
    """Ensure every item in every puzzle has the correct type."""
    def setUp(self):
        ui.CLI()  # populate session variables

    def test_alldevices(self):
        for puz in session.puzzlelist:
            p = puzzle.Puzzle(puz.get('EduNetworkBuilder').get('Network'))
            devs = p.all_devices()
            for dev in devs:
                self.assertIsInstance(dev, dict)

    def test_alllinks(self):
        for puz in session.puzzlelist:
            p = puzzle.Puzzle(puz)
            links = p.all_links()
            for link in links:
                self.assertIsInstance(link, dict)


class TestInit(unittest.TestCase):
    def setUp(self):
        self.data = {
            'a': 'all',
            'g': 'good',
            'hostname': 'test'
        }

    def test_baddata(self):
        self.assertRaises(ValueError, puzzle.Puzzle, 'fake')

    def test_gooddata(self):
        self.assertEqual(self.data, puzzle.Puzzle(self.data).json)

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
        self.puzzle_name = 'Level0_HubVsSwitch'

        # Load puzzle via app into session.puzzle.
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

    def test_devicefromname_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.device_from_name('net_hub0').get('uniqueidentifier')
        )

    def test_devicefromname_notfound(self):
        self.assertIsNone(session.puzzle.device_from_name('supercool_dev9'))

    def test_devicefromuid_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.device_from_uid('160').get('uniqueidentifier')
        )

    def test_devicefromuid_notfound(self):
        self.assertIsNone(session.puzzle.device_from_uid('999'))

    def test_itemfromuid_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.item_from_uid('160').get('uniqueidentifier')
        )

    def test_itemfromuid_notfound(self):
        self.assertIsNone(session.puzzle.item_from_uid('999'))

    def test_linkfromdevices_found(self):
        self.assertEqual(
            self.link0.get('uniqueidentifier'),
            session.puzzle.link_from_devices(self.device1, self.device4).get('uniqueidentifier')
        )

    def test_linkfromdevices_notfound(self):
        self.assertIsNone(session.puzzle.link_from_devices(self.device0, self.device1))

    def test_linkfromuid_found(self):
        self.assertEqual(
            self.link0,
            session.puzzle.link_from_uid('146'))

    def test_linkfromuid_notfound(self):
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