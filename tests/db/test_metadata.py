import os
import unittest
from datetime import datetime, timedelta

from parameterized import parameterized

from pdst.db.metadata import BaseMetadata, MetadataType, EpisodeMetadata


class TestMetadata(unittest.TestCase):
    testData = {'id': 10,
                'library_section_id': 7,
                'metadata_type': 4,
                'guid': 'aGuIdABCDEF123',
                'title': 'Test Title',
                'summary': 'Summary',
                'tags_genre': 'Tag A|Tag B',
                'year': 2020,
                'duration': 9000000,
                'user_thumb_url': 'upload://posters/383a16a39f9e3302e4608572a7ee14f3d103ee17.jpg',
                'originally_available_at': '2020-02-03 08:07:06',
                'added_at': '2020-04-05 06:07:08',
                'created_at': '2020-10-11 12:13:14',
                'index': None,
                'hash': 'deadbeef123',
                'parent_id': 9}

    datetime_iso_format = '%Y-%m-%d %H:%M:%S'

    def test_BaseMetadata_init(self):
        row = self.testData

        metadata = BaseMetadata(row)
        self.assertMatchesTestData(metadata)

    def assertMatchesTestData(self, metadata):
        self.assertEqual(10, metadata.id)
        self.assertEqual(7, metadata.libraryId)
        self.assertEqual(9, metadata.parentId)
        self.assertEqual('aGuIdABCDEF123', metadata.guid)
        self.assertEqual(MetadataType.EPISODE, metadata.type)

        self.assertIsNone(metadata.index)
        self.assertEqual('upload://posters/383a16a39f9e3302e4608572a7ee14f3d103ee17.jpg', metadata.thumbUrl)

        self.assertEqual('Test Title', metadata.title)
        self.assertEqual('Summary', metadata.summary)
        self.assertIn('Tag A', metadata.tags)
        self.assertIn('Tag B', metadata.tags)
        self.assertEqual(2020, metadata.year)
        self.assertEqual('deadbeef123', metadata.hash)
        self.assertEqual(timedelta(hours=2.5), metadata.duration)
        self.assertEqual(datetime(2020, 2, 3, 8, 7, 6), metadata.originallyAvailable)
        self.assertEqual(datetime(2020, 4, 5, 6, 7, 8), metadata.added)
        self.assertEqual(datetime(2020, 10, 11, 12, 13, 14), metadata.created)

    def test_EpisodeMetadata_init(self):
        row = self.testData
        row['extra_data'] = 'at%3AchannelIdentifier=1060&at%3AmediaGrabBeginsAt=1595781000&at%3AData=asdfqwerty'

        metadata = EpisodeMetadata(row)
        self.assertMatchesTestData(metadata)

        self.assertEqual(datetime(2020, 4, 5, 3, 37, 8), metadata.recordingStarted)
        self.assertEqual(datetime.fromtimestamp(1595781000), metadata.mediaGrabBegan)

    def test_Metadata_ToFromFile(self):
        showData = {'id': 8,
                    'library_section_id': 7,
                    'metadata_type': 2,
                    'guid': 'anotherGuiD',
                    'title': 'The Show',
                    'summary': 'Show Summary',
                    'tags_genre': 'Tag A|Tag B',
                    'year': 2020,
                    'duration': None,
                    'index': None,
                    'hash': '987654bcd',
                    'parent_id': None}
        show = BaseMetadata(showData)
        metadata = EpisodeMetadata(self.testData, showMetadata=show)

        testsDir = os.path.normpath(os.path.join(os.path.split(__file__)[0], '..'))
        filePath = os.path.join(testsDir, 'test-files', 'test_metadata.metadata')

        metadata.writeToFile(filePath)

        readMetadata = EpisodeMetadata.fromFile(filePath)

        self.assertMatchesTestData(readMetadata)

        self.assertEqual(8, readMetadata.show.id)
        self.assertEqual('The Show', readMetadata.show.title)

        os.remove(filePath)

    @parameterized.expand([
        ('2020-06-01 12:00:00', None, None, None,
            '2020-06-01 12:00:00'),
        (None, timedelta(hours=2), '2020-06-02 13:00:00', None,
            '2020-06-02 11:00:00'),
        (None, None, None, '2020-06-03 13:00:00',
            '2020-06-03 13:00:00'),
        ('2020-06-01 12:00:00', timedelta(hours=2), '2020-06-02 13:00:00', '2020-06-03 13:10:00',
            '2020-06-03 12:00:00')
    ])
    def test_Metadata_getTimestamp(self, grabBegan, duration, added, originallyAvailable, expected):
        durationMs = duration / timedelta(milliseconds=1) if duration is not None else None
        grabBeganMs = datetime.strptime(grabBegan, self.datetime_iso_format).timestamp() if grabBegan is not None else None
        extraDataString = f'mediaGrabBeginsAt={grabBeganMs}'
        data = {'originally_available_at': originallyAvailable,
                'added_at': added,
                'duration': durationMs,
                'extra_data': extraDataString}
        metadata = EpisodeMetadata(data)

        expectedDatetime = datetime.strptime(expected, self.datetime_iso_format)
        self.assertEqual(expectedDatetime, metadata.getOriginalTimestampGuess())

    def test_Metadata_getTimestamp_releaseOverride(self):
        durationMs = timedelta(hours=2) / timedelta(milliseconds=1)
        grabBeganMs = datetime.strptime('2020-06-01 12:00:00', self.datetime_iso_format).timestamp()
        extraDataString = f'mediaGrabBeginsAt={grabBeganMs}'
        data = {'originally_available_at': '2020-06-01 12:00:00',
                'added_at': '2020-06-01 12:00:00',
                'duration': durationMs,
                'extra_data': extraDataString,
                'release': '2020-08-02',
                'releaseTime': '09:10:11'}
        metadata = EpisodeMetadata(data)

        expectedDatetime = datetime.strptime('2020-08-02 09:10:11', self.datetime_iso_format)
        self.assertEqual(expectedDatetime, metadata.getOriginalTimestampGuess())
