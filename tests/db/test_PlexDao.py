import os
import unittest

from pdst.db.PlexDao import PlexDao
from pdst.db.metadata import MetadataType


class TestPlexDao(unittest.TestCase):

    def setUp(self):
        testsDir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
        libPath = os.path.join(testsDir, 'test-files', 'testPlexLibrary')
        self.db = PlexDao(libPath)

    def test_getMetadataForEpisodeFile(self):
        filePath = '/a/fake/data/path/Sport Alpha (2009)/Season 2020/Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts'
        metadata = self.db.getMetadataForEpisodeFile(filePath)

        self.assertIsNotNone(metadata)
        self.assertEqual(3, metadata.id)
        self.assertEqual('Team Alpha vs. Team Bravo', metadata.title)
        self.assertEqual('A match between Team Alpha and Team Bravo', metadata.summary)
        self.assertIn('Sport', metadata.tags)
        self.assertIn('Alpha', metadata.tags)
        self.assertEqual('abc123', metadata.hash)

        self.assertEqual(MetadataType.SEASON, metadata.season.type)
        self.assertEqual(MetadataType.SHOW, metadata.show.type)

        self.assertEqual('Sport Alpha', metadata.show.title)
        self.assertEqual(2020, metadata.season.index)
