import os
import unittest
from pathlib import Path

from parameterized import parameterized

from pdst.Config import Config, SportConfigEntry, DateOverrideMode, SportMatchEntry
from pdst.db.metadata import EpisodeMetadata


class TestConfig(unittest.TestCase):

    def test_Config_sample(self):
        testsDir = Path(os.path.split(__file__)[0])
        jsonPath = os.path.join(testsDir, 'test-files', 'test_sports.json')
        config = Config(jsonPath)

        self.assertTrue(len(config.sports) > 0, 'Sports parsed from Config should not be empty')

    @parameterized.expand([
        ('always', DateOverrideMode.ALWAYS),
        (None, DateOverrideMode.EOY),
        ('EoY', DateOverrideMode.EOY),
        ('NEVER', DateOverrideMode.NEVER)
    ])
    def test_Config_SportEntry_dateOverride(self, configMode, expected):
        sportEntry = {
            'name': 'Test Sport'
        }
        if configMode is not None:
            sportEntry['dateOverride'] = configMode

        entry = SportConfigEntry(sportEntry)

        self.assertEqual(expected, entry.dateOverride)

    @parameterized.expand([
        ('Plain String', 'Plain[\\s\\.\\-_]+String'),
        ({'match': 'Dict'}, 'Dict'),
    ])
    def test_Config_SportMatchEntry_init_regex(self, inEntry, expectedMatchRegex):
        entry = SportMatchEntry(inEntry)
        self.assertEqual(expectedMatchRegex, entry.matchRegex)

    @parameterized.expand([
        ({'rawRegex': 'Raw Regex 123'}, 'Raw Regex 123'),
        ({'match': 'match', 'rawRegex': 'Raw Regex 123'}, 'Raw Regex 123'),
    ])
    def test_Config_SportMatchEntry_init_rawRegex(self, inEntry, expectedMatchRegex):
        entry = SportMatchEntry(inEntry)
        self.assertEqual(expectedMatchRegex, entry.matchRegex)

    @parameterized.expand([
        ('match', None),
        ({'match': 'match'}, None),
        ({'match': 'match', 'overrideShow': True}, True),
        ({'match': 'match', 'overrideShow': 'Another Show'}, 'Another Show'),
    ])
    def test_Config_SportMatchEntry_init_overrideShow(self, inEntry, expectedOverride):
        entry = SportMatchEntry(inEntry)
        self.assertEqual(expectedOverride, entry.overrideShow)

    @parameterized.expand([
        ({'name': 'Sport'}, None, None),
        ({'name': 'Sport', 'imageTextRegex': r'(Game \d+):'}, None, None),
        ({'name': 'Sport', 'imageTextRegex': r'(Game \d+):'}, {'title': 'Game 7: A v. B'}, 'Game 7'),
        ({'name': 'Sport', 'imageTextRegex': r'(Game \d+):'}, {'title': 'A v. B'}, None),
    ])
    def test_Config_SportConfigEntry_getImageTextFor(self, config, inMetadata, expectedText):
        entry = SportConfigEntry(config)
        metadata = EpisodeMetadata(inMetadata) if inMetadata is not None else None
        text = entry.getImageTextFor(metadata)
        self.assertEqual(expectedText, text)
