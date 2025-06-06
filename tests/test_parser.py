from network_puzzles import parser
import unittest


class TestParse(unittest.TestCase):
    def setUp(self):
        self.parser = parser.Parser()

    def test_command_invalid(self):
        cmds = [
            'help',
            'foo bar',
            '',
        ]
        for cmd in cmds:
            self.assertIsNone(self.parser.parse(cmd))

    def test_search_caseinsensitive(self):
        self.assertEqual(self.parser.parse('search dhcp'), self.parser.parse('search DHCP'))

    def test_search_valid(self):
        cmds = [
            'search dhcp',
            'search DHCP',
            'puzzles vlan',
            'puzzles',
        ]
        for cmd in cmds:
            r = self.parser.parse(cmd)
            self.assertIsInstance(r, dict)
            self.assertTrue(len(r.get('value')) > 0)
            self.assertTrue(r.get('command') in ['puzzles', 'search'])
    
    def test_search_noresults(self):
        cmds = [
            'search none',
            'puzzles 999'
        ]
        for cmd in cmds:
            self.assertEqual(0, len(self.parser.parse(cmd).get('value')))