import re
from datetime import datetime, timedelta, date, time
from enum import IntEnum

from pdst import parsing


class MetadataType(IntEnum):
    SHOW = 2,
    SEASON = 3,
    EPISODE = 4


def convertToIntOrNone(rowData, key):
    try:
        result = int(rowData[key])
    except (TypeError, ValueError, KeyError):
        result = None
    return result


def byKeyOrNone(rowData, key):
    try:
        result = rowData[key]
    except (KeyError, IndexError):
        result = None
    return result


class BaseMetadata:

    def __init__(self, rowData):
        if rowData is not None:
            self.id = convertToIntOrNone(rowData, 'id')
            self.libraryId = convertToIntOrNone(rowData, 'library_section_id')
            self.parentId = convertToIntOrNone(rowData, 'parent_id')

            typeNum = convertToIntOrNone(rowData, 'metadata_type')
            self.type = MetadataType(typeNum) if typeNum is not None else None
            self.guid = byKeyOrNone(rowData, 'guid')

            title = byKeyOrNone(rowData, 'title')
            self.title = parsing.removeYears(title)
            self.summary = byKeyOrNone(rowData, 'summary')

            tags = byKeyOrNone(rowData, 'tags_genre')
            self.tags = tags.split('|') if tags is not None else []

            self.year = convertToIntOrNone(rowData, 'year')
            self.index = convertToIntOrNone(rowData, 'index')

            self.thumbUrl = byKeyOrNone(rowData, 'user_thumb_url')
            self.hash = byKeyOrNone(rowData, 'hash')

            duration = convertToIntOrNone(rowData, 'duration')
            self.duration = timedelta(milliseconds=duration) if duration is not None else None

            plex_timestamp_format = '%Y-%m-%d %H:%M:%S'

            origAvail = byKeyOrNone(rowData, 'originally_available_at')
            self.originallyAvailable = datetime.strptime(origAvail, plex_timestamp_format) \
                if origAvail is not None else None

            added = byKeyOrNone(rowData, 'added_at')
            self.added = datetime.strptime(added, plex_timestamp_format) \
                if added is not None else None

            created = byKeyOrNone(rowData, 'created_at')
            self.created = datetime.strptime(created, plex_timestamp_format) \
                if created is not None else None

            release = byKeyOrNone(rowData, 'release')
            releaseTime = byKeyOrNone(rowData, 'releaseTime')
            if release is not None and releaseTime is not None:
                self.release = datetime.strptime(f"{release} {releaseTime}", plex_timestamp_format)
            else:
                self.release = None

            self.parent = None


class EpisodeMetadata(BaseMetadata):

    def __init__(self, rowData, seasonMetadata=None, showMetadata=None):
        super().__init__(rowData)

        self.recordingStarted = None

        if self.added is not None and self.duration is not None:
            self.recordingStarted = self.added - self.duration

        self.mediaGrabBegan = None
        self.extraData = byKeyOrNone(rowData, 'extra_data')
        self.partExtraData = byKeyOrNone(rowData, 'part_extra_data')

        if self.extraData is not None:
            grabBegin = re.search(r'mediaGrabBeginsAt=(\d+)', self.extraData, re.IGNORECASE)
            if grabBegin is not None:
                timestamp = grabBegin.groups(1)[0]
                self.mediaGrabBegan = datetime.fromtimestamp(int(timestamp))

        self.season = seasonMetadata
        self.show = showMetadata

    def getOriginalTimestampGuess(self):
        # better TIME data
        bestTimesOrder = [self.release, self.mediaGrabBegan, self.recordingStarted, self.added, self.originallyAvailable]
        bestTime = next((item for item in bestTimesOrder if item is not None), None)

        bestDatesOrder = [self.release, self.originallyAvailable, self.mediaGrabBegan, self.recordingStarted, self.added]
        bestDate = next((item for item in bestDatesOrder if item is not None), None)

        if bestTime is None or bestDate is None:
            return bestTime if bestDate is None else bestDate

        combined = datetime.combine(bestDate.date(), bestTime.time())
        return combined

    def writeToFile(self, file):
        with open(file, 'w') as out:
            print('[metadata]', file=out)
            print(f"title={self.title}", file=out)
            print(f"summary={self.summary}", file=out)

            ts = self.getOriginalTimestampGuess()
            if ts is not None:
                print(f"release={ts.strftime('%Y-%m-%d')}", file=out)
                print(f"releaseTime={ts.strftime('%H:%M:%S')}", file=out)

            print(f"tags={';'.join(self.tags)}", file=out)
            print(f"year={self.year}", file=out)

            print(file=out)

            print(f"id={self.id}", file=out)
            print(f"library_section_id={self.libraryId}", file=out)
            print(f"metadata_type={self.type}", file=out)
            print(f"guid={self.guid}", file=out)
            print(f"tags_genre={'|'.join(self.tags)}", file=out)
            print(f"duration={int(self.duration / timedelta(milliseconds=1))}", file=out)
            print(f"user_thumb_url={self.thumbUrl}", file=out)
            print(f"originally_available_at={self.originallyAvailable}", file=out)
            print(f"added_at={self.added}", file=out)
            print(f"created_at={self.created}", file=out)
            print(f"index={self.index}", file=out)
            print(f"hash={self.hash}", file=out)
            print(f"parent_id={self.parentId}", file=out)
            print(f"extra_data={self.extraData}", file=out)
            print(f"part_extra_data={self.partExtraData}", file=out)

            if self.season is not None:
                print('', file=out)
                print('[Season]', file=out)
                print(f"id={self.season.id}", file=out)
                print(f"index={self.season.index}", file=out)
                print(f"hash={self.season.hash}", file=out)
                print(f"parent_id={self.season.parentId}", file=out)

            if self.show is not None:
                print('', file=out)
                print('[Show]', file=out)
                print(f"title={self.show.title}", file=out)
                print(f"summary={self.show.summary}", file=out)
                print(f"id={self.show.id}", file=out)
                print(f"user_thumb_url={self.show.thumbUrl}", file=out)
                print(f"index={self.show.index}", file=out)
                print(f"hash={self.show.hash}", file=out)
                print(f"parent_id={self.show.parentId}", file=out)

    @staticmethod
    def fromFile(filename):
        data = {}
        showData = {}
        seasonData = {}

        currentData = data
        with open(filename) as f:
            for line in f:
                if '[metadata]' in line:
                    currentData = data
                elif '[Season]' in line:
                    currentData = seasonData
                elif '[Show]' in line:
                    currentData = showData

                if '=' in line:
                    split = line.strip().split('=')
                    currentData[split[0]] = split[1]

        seasonMetadata = BaseMetadata(seasonData)
        showMetadata = BaseMetadata(showData)
        return EpisodeMetadata(data, seasonMetadata=seasonMetadata, showMetadata=showMetadata)
