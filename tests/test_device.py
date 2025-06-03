import json
import unittest
from network_puzzles import device
from network_puzzles import session
from network_puzzles import ui
from . import PUZZLES_DIR


class TestAllDevicesAndLinks(unittest.TestCase):
    @unittest.skip("not implemented")
    def test_alldevices(self):
        pass

    @unittest.skip("not implemented")
    def test_alllinks(self):
        pass


class TestGetItemByAttrib(unittest.TestCase):
    def setUp(self):
        self.items = [
            {'name': 'item1', 'uid': '0'},
            {'name': 'item2', 'uid': '1'},
        ]

        # TODO: Use Mock rather than "real" session.puzzle.
        self.puzzle_name = 'Level0-HubVsSwitch'

        # Load puzzle via app in to session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle
    
    def test_found(self):
        self.assertEqual(self.items[0], session.puzzle._item_by_attrib(self.items, 'name', 'item1'))

    def test_notfound(self):
        self.assertIsNone(session.puzzle._item_by_attrib(self.items, 'uid', '3'))


class TestXFromY(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = 'Level0-HubVsSwitch'
        # Load puzzle data separately via json.load.
        puzzle_file = PUZZLES_DIR / f'{self.puzzle_name}.json'
        with puzzle_file.open() as f:
            self.puzzle = json.load(f)  # gets independent puzzle data from file
        self.network = self.puzzle.get('EduNetworkBuilder').get('Network')

        self.device0 = self.network.get('device')[0]  # net_hub0
        self.nic00 = self.device0.get('nic')[0]

    def test_nicfromname_found(self):
        self.assertEqual(
            self.nic00,
            device.Device(self.device0).nic_from_name('lo0')
        )

    def test_nicfromname_notfound(self):
        self.assertIsNone(device.Device(self.device0).nic_from_name('eth99'))