from datetime import datetime
import logging
import os

from pdst import filetools
from pdst.Config import DateOverrideMode
from pdst.db.metadata import EpisodeMetadata

log = logging.getLogger(__name__)


class MetadataService:

    def __init__(self, plexDao, sportService):
        self.plexDao = plexDao
        self.sportService = sportService

    def getMetadataForEpisodeFile(self, filePath, readFromFile=True):
        log.debug(f"Getting Metadata for {filePath}")

        if readFromFile:
            metadataFile = filetools.getMetadataFilename(filePath)
            if os.path.exists(metadataFile):
                metadata = EpisodeMetadata.fromFile(metadataFile)
                if metadata is not None:
                    return metadata
            else:
                log.debug(f"{filePath} doesn't have an existing metadata file, checking DB...")

        metadata = self.plexDao.getMetadataForEpisodeFile(filePath)

        if metadata is None:  # pragma: no cover
            if not readFromFile:
                log.debug(f"No metadata found in DB for {filePath}, but did not check for existing metadata file")
            else:
                log.warning(f"NO metadata found in db or metadata file for {filePath}!")

            return None

        # Fix empty title
        if metadata.title is None or len(metadata.title.strip()) == 0:
            parts = os.path.splitext(os.path.basename(filePath))[0].split(' - ')
            if len(parts) > 2:
                metadata.title = parts[2]

        if metadata.show is None:
            log.debug(f"Metadata does not include show data!")
            searchString = filePath
        else:
            searchString = metadata.show.title

        sportEntry = self.sportService.getSportFor(searchString)

        if sportEntry is not None:
            log.debug(f"Sport Config Entry: {sportEntry.name}")
            if self.__shouldOverrideDate(metadata, sportEntry):
                bestDatesOrder = [metadata.mediaGrabBegan, metadata.recordingStarted, metadata.added]
                bestDate = next((item for item in bestDatesOrder if item is not None), None)
                log.debug(f"Overriding original availability to: {bestDate}")
                metadata.originallyAvailable = datetime.combine(bestDate.date(), metadata.originallyAvailable.time())
                metadata.season.index = bestDate.year

            sportOverrideShow = sportEntry.overrideShow
            if sportOverrideShow:
                newShow = sportOverrideShow if isinstance(sportOverrideShow, str) else sportEntry.name
                metadata.show.title = newShow

            match, score = sportEntry.matchObjectFor(searchString)
            log.debug(f"Match entry: {match}")
            if match is not None and match.overrideShow:
                newShow = match.overrideShow if isinstance(match.overrideShow, str) else sportEntry.name
                metadata.show.title = newShow

        return metadata

    def __shouldOverrideDate(self, metadata, sportEntry):
        if sportEntry.dateOverride == DateOverrideMode.NEVER:
            return False

        if sportEntry.dateOverride == DateOverrideMode.ALWAYS:
            return True

        # DateTimeMode.EOY
        release = metadata.release
        if release is not None and release.month == 12 and release.day == 31:
            return True
