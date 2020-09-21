import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from parameterized import parameterized

from pdst.Config import DateOverrideMode, SportConfigEntry
from pdst.MetadataService import MetadataService


class TestCliMetadataExport(unittest.TestCase):

    def setUp(self):
        self.mockDao = MagicMock()
        self.mockSportService = MagicMock()

        sportConfig = MagicMock()
        sportConfig.matchObjectFor.return_value = MagicMock(), 0
        self.mockSportService.getSportFor.return_value = sportConfig

        self.service = MetadataService(self.mockDao, self.mockSportService)

    def test_getMetadataForEpisodeFile_noTitle(self):
        metadata = self.service.getMetadataForEpisodeFile('Sport - 2020-08-01 - The Title.ts')

        self.assertEqual('The Title', metadata.title)

    def test_getMetadataForEpisodeFile_overrideDate(self):
        dbMetadata = MagicMock()
        original = datetime(2019, 12, 31, 12, 0, 0)
        dbMetadata.release = original
        dbMetadata.originallyAvailable = original
        dbMetadata.mediaGrabBegan = datetime(2020, 8, 1, 12, 0, 0)

        sportConfig = MagicMock()
        sportConfig.dateOverride = DateOverrideMode.EOY
        sportConfig.matchObjectFor.return_value = MagicMock(), 0

        self.mockDao.getMetadataForEpisodeFile.return_value = dbMetadata
        self.mockSportService.getSportFor.return_value = sportConfig
        metadata = self.service.getMetadataForEpisodeFile('Sport - 2019-12-31 - The Title.ts')

        self.assertEqual(2020, metadata.originallyAvailable.year)
        self.assertEqual(8, metadata.originallyAvailable.month)
        self.assertEqual(1, metadata.originallyAvailable.day)
        self.assertEqual(2020, metadata.season.index)

    @parameterized.expand([
        ('Original Show', {'name': 'Sport Name'}, 'Original Show'),
        ('Original Show', {'name': 'Sport Name', 'matches': ['Show']}, 'Original Show'),
        ('Original Show', {'name': 'Sport Name', 'matches': [{'match': 'Show', 'overrideShow': False}]}, 'Original Show'),
        ('Original Show', {'name': 'Sport Name', 'matches': ['Show', {'match': 'Not', 'overrideShow': True}]}, 'Original Show'),
        ('Original Show', {'name': 'Sport Name', 'matches': [{'match': 'Show', 'overrideShow': True}]}, 'Sport Name'),
        ('Original Show', {'name': 'Sport Name', 'matches': [{'match': 'Show', 'overrideShow': 'Match Show'}]}, 'Match Show'),
        ('Original Show', {'name': 'Sport Name', 'overrideShow': False}, 'Original Show'),
        ('Original Show', {'name': 'Sport Name', 'overrideShow': True}, 'Sport Name'),
        ('Original Show', {'name': 'Sport Name', 'overrideShow': 'Override Show'}, 'Override Show'),
        ('Original Show', {'name': 'Sport Name', 'overrideShow': 'Override Show',
          'matches': [{'match': 'Show', 'overrideShow': 'Match Show'}]}, 'Match Show'),
        ('Original Show', {'name': 'Sport Name', 'overrideShow': 'Override Show',
          'matches': ['Show', {'match': 'Should not match', 'overrideShow': 'Match Show'}]}, 'Override Show'),
        ('UEFA Champions League Soccer', {'name': 'UEFA', 'matches': [
            {'match': 'UEFA Champions', 'overrideShow': 'UEFA Champions League'},
            {'match': 'UEFA Europa', 'overrideShow': 'UEFA Europa League'},
            'UEFA'
            ]}, 'UEFA Champions League'),
        ('UEFA Something', {'name': 'UEFA', 'overrideShow': 'sport override', 'matches': [
            {'match': 'UEFA Champions', 'overrideShow': 'UEFA Champions League'},
            {'match': 'UEFA Europa', 'overrideShow': 'UEFA Europa League'},
            'UEFA'
            ]}, 'sport override'),
    ])
    def test_getMetadataForEpisodeFile_overrideShow(self, originalShow, sportConfig, expectedShow):
        dbMetadata = MagicMock()
        dbMetadata.show.title = originalShow

        self.mockDao.getMetadataForEpisodeFile.return_value = dbMetadata

        sportConfig = SportConfigEntry(sportConfig)
        self.mockSportService.getSportFor.return_value = sportConfig

        metadata = self.service.getMetadataForEpisodeFile('Original Show - 2019-12-31 - The Title.ts')

        self.assertEqual(expectedShow, metadata.show.title)

    @patch('pdst.MetadataService.os.path.exists', return_value=True)
    @patch('pdst.db.metadata.EpisodeMetadata.fromFile')
    def test_getMetadataForEpisodeFile_hasMetadataFile(self, mockMetadataFromFile, mockPathExists):
        """Prefer metadata file over DB metadata if present"""
        dbMetadata = MagicMock()
        dbMetadata.show.title = 'DB Show'

        self.mockDao.getMetadataForEpisodeFile.return_value = dbMetadata

        fileMetadata = MagicMock()
        fileMetadata.show.title = 'File Show'
        mockMetadataFromFile.return_value = fileMetadata

        metadata = self.service.getMetadataForEpisodeFile('Sport - 2019-12-31 - The Title.ts')

        self.assertEqual('File Show', metadata.show.title)
