import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from parameterized import parameterized

from pdst import filetools


class TestMetadata(unittest.TestCase):

    def test_getBetterFilename_no_timestamp(self):
        mockShow = MagicMock()
        mockShow.title = 'Show Name'

        metadata = MagicMock()
        metadata.show = mockShow
        metadata.release = None
        metadata.title = 'Show Title'

        name = filetools.getBetterFilename(metadata)

        self.assertEqual("Show Name - Show Title", name)

    def test_getBetterFilename_no_show_no_ts(self):
        metadata = MagicMock()
        metadata.show = None
        metadata.release = None
        metadata.title = 'Show Title'

        name = filetools.getBetterFilename(metadata)

        self.assertEqual("Show Title", name)

    def test_getBetterFilename(self):
        mockShow = MagicMock()
        mockShow.title = 'Show Name'

        metadata = MagicMock()
        metadata.show = mockShow
        metadata.release = datetime(2020, 1, 2, 3, 4, 5)
        metadata.title = 'Show Title'

        name = filetools.getBetterFilename(metadata)

        self.assertEqual("Show Name - 2020-01-02 03 04 05 - Show Title", name)

    def test_getBetterFilename_bad_chars(self):
        mockShow = MagicMock()
        mockShow.title = 'Show: Name'

        metadata = MagicMock()
        metadata.show = mockShow
        metadata.release = None
        metadata.title = 'Show? Title| and* some" [other] stuff/\\%<>\''

        name = filetools.getBetterFilename(metadata)

        self.assertEqual("Show Name - Show Title and some other stuff", name)

    @parameterized.expand([
        ('None', 'None'),
        ('àéêöhello', 'aeeohello'),
        ('Beşiktaş', 'Besiktas'),
        ('Saint-Étienne', 'Saint-Etienne'),
        ('Liège', 'Liege'),
        ('İstanbul Başakşehir', 'Istanbul Basaksehir'),
        ('Nikšić', 'Niksic'),
    ])
    def test_convertUnicodeChars(self, inStr, expected):
        out = filetools.convertUnicodeChars(inStr)

        self.assertEqual(expected, out)

    @parameterized.expand([
        (None, 'hash123', None),
        ('upload://posters/123.jpg', 'hash123', 'Metadata/TV Shows/h/ash123.bundle/Uploads/posters/123.jpg'),
        # ('media://', 'hash123', None),
        # ('metadata://', 'hash123', None),
    ])
    def test_getRealThumbPath(self, thumbUrl, hash, expected):
        metadata = MagicMock()
        metadata.thumbUrl = thumbUrl
        metadata.hash = hash

        output = filetools.getRealThumbPath(metadata)
        expected_osPathSep_fixed = os.path.sep.join(expected.split('/')) if expected is not None else None
        self.assertEqual(expected_osPathSep_fixed, output)

    @parameterized.expand([
        ('Show - 2020-01-01 12 00 00 - Title', '2020-01-01 12:00:00'),
        ('2020-01-01 12 00 00 - Title', '2020-01-01 12:00:00'),
    ])
    def test_getTimestampFromFilename(self, inFilename, expected):
        expectedDt = datetime.strptime(expected, '%Y-%m-%d %H:%M:%S')

        outDt = filetools.getTimestampFromFilename(inFilename)
        self.assertEqual(expectedDt, outDt)

    @parameterized.expand([
        ('File.txt',
         {'show': 'Show', 'title': 'Title',
          'release': datetime.strptime('2020-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')},
         [], 'Show - 2020-01-01 12 00 00 - Title'),
        ('File.txt',
         {'show': 'Show', 'title': 'Title',
          'release': datetime.strptime('2020-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')},
         ['Show - 2020-01-01 12 00 00 - Another.mkv'],
         'Show - 2020-01-01 12 00 01 - Title'),
        ('Show - 2020-01-01 12 00 00 - Original.mkv',
         {'show': 'Show', 'title': 'Title',
          'release': datetime.strptime('2020-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')},
         ['Show - 2020-01-01 12 00 00 - Original.mkv'],
         'Show - 2020-01-01 12 00 00 - Title'),
        ('Show - 2020-01-01 12 00 00 - Original.mkv',
         {'show': 'Show', 'title': 'Title',
          'release': datetime.strptime('2020-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')},
         ['Show - 2020-01-01 12 00 00 - Original.mkv',
          'Show - 2020-01-01 12 00 00 - Other.mkv'],
         'Show - 2020-01-01 12 00 01 - Title'),
        ('File.txt',
         {'show': 'Show', 'title': 'Title',
          'release': datetime.strptime('2020-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')},
         ['Show - 2020-01-01 12 00 00 - Another.mkv',
          'Show - 2020-01-01 12 00 01 - Another2.mkv'],
         'Show - 2020-01-01 12 00 02 - Title'),
    ])
    @patch('pdst.filetools.os.scandir')
    def test_getMoveDestinationFilename(self, originalFile, metadata, otherFilesInDestination, expectedName, scanMock):
        destinationPath = '/a/fake/path'
        scanMock.return_value = otherFilesInDestination

        metadataObj = MagicMock()
        mockShow = MagicMock()
        mockShow.title = metadata['show']
        metadataObj.show = mockShow
        metadataObj.title = metadata['title']
        metadataObj.release = metadata['release']

        output = filetools.getMoveDestinationFilename(originalFile, metadataObj, destinationPath)
        self.assertEqual(expectedName, output)
