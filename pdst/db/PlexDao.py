import logging
import os
import sqlite3

from pdst.db.metadata import MetadataType, BaseMetadata, EpisodeMetadata

log = logging.getLogger(__name__)


class PlexDao:

    PLEX_DB_PATH = os.path.join('Plug-in Support', 'Databases', 'com.plexapp.plugins.library.db')

    def __init__(self, libraryPath):
        self.dbPath = self.PLEX_DB_PATH
        if libraryPath is not None:
            self.dbPath = os.path.join(libraryPath, self.PLEX_DB_PATH)

    def __getDbCursor(self):
        conn = sqlite3.connect(self.dbPath)
        conn.row_factory = sqlite3.Row
        return conn.cursor()

    def getMetadataForEpisodeFile(self, filePath):
        log.debug(f"Getting Metadata from DB for {filePath}")

        cursor = self.__getDbCursor()

        cursor.execute("""SELECT 
            meta.id,
            meta.library_section_id,
            meta.parent_id,
            meta.metadata_type,
            meta.guid,
            meta.title,
            meta.summary,
            meta.tags_genre as genres,
            meta.year,
            meta."index",
            meta.user_thumb_url,
            meta.duration,
            meta.originally_available_at,
            meta.added_at,
            meta.created_at,
            meta.hash,
            mi.extra_data,
            mp.extra_data as part_extra_data
            from media_parts mp
            join media_items mi on mi.id = mp.media_item_id
            join metadata_items meta on meta.id = mi.metadata_item_id
            where mp.file=?""", [filePath])

        result = cursor.fetchone()

        metadata = None
        if result is None:
            log.info(f"Did not find a matching media_part entry for {filePath}")
        else:
            if result['metadata_type'] != MetadataType.EPISODE:
                log.warning(f"Metadata for {filePath} is somehow NOT an episode??")
            else:
                epRow = result
                season = None
                show = None

                parentId = result['parent_id']
                while parentId is not None:
                    parent = self.__getMetadataById(parentId, cursor)
                    if parent.type == MetadataType.SEASON:
                        season = parent
                    elif parent.type == MetadataType.SHOW:
                        show = parent
                    else:
                        log.warning(f"Unable to get metadata for {parentId}!")
                        log.warning(f"Got: {parent}")

                    parentId = parent.parentId

                metadata = EpisodeMetadata(epRow, season, show)

        return metadata

    def __getMetadataById(self, metadataId, cursor):
        cursor.execute("""SELECT 
            id,
            library_section_id,
            parent_id,
            metadata_type,
            guid,
            title,
            summary,
            tags_genre as genres,
            year,
            "index",
            user_thumb_url,
            duration,
            originally_available_at,
            added_at,
            created_at,
            hash
            from metadata_items
            where id=?""", [metadataId])

        result = cursor.fetchone()

        metadata = None
        if result is not None:
            metadata = BaseMetadata(result)

        return metadata
