import glob
import logging
import os

from unidecode import unidecode

from pdst import parsing

log = logging.getLogger(__name__)


def getBetterFilename(metadata):
    showTitle = None
    if metadata.show is not None:
        showTitle = metadata.show.title

    timestamp = metadata.getOriginalTimestampGuess()
    timeString = None
    if timestamp is not None:
        timeString = timestamp.strftime('%Y-%m-%d %H %M %S')

    parts = [p for p in [showTitle, timeString, metadata.title] if p is not None]
    filename = ' - '.join(parts)

    cleaned = parsing.removeBadFilenameChars(filename)
    unaccented = convertUnicodeChars(cleaned)

    return unaccented


def convertUnicodeChars(inStr):
    return unidecode(inStr)


def getRealThumbPath(metadata):
    """Returns the actual filepath relative to the Plex Library root for the thumbnail image"""
    log.debug(f"Getting real thumbnail path for {metadata.thumbUrl}")
    thumbUrl = metadata.thumbUrl
    if thumbUrl is None:
        return None

    path = thumbUrl

    if thumbUrl.startswith('upload://'):
        upload = thumbUrl[9:]
        uploadOsFixed = os.path.join(*upload.split('/'))
        hashStr = metadata.hash

        path = os.path.join('Metadata', 'TV Shows', hashStr[:1], hashStr[1:] + '.bundle', 'Uploads', uploadOsFixed)

    return path


def getSubdirs(path):
    """Returns a list of subdirectory names under the given dir that are not set to be ignored"""
    return [f.name for f in os.scandir(path) if notIgnoredDir(f)]


def getImageFilesInDir(path):
    """Returns a list of DirEntries for images under the given directory

    Does not go into subdirectories - for that use getAllImagesFilesInHierarchy
    """
    return [f for f in os.scandir(path) if shouldReturnFile(f, ['png', 'gif', 'jpg', 'jpeg'])]


def notIgnoredDir(dirEntry):
    return dirEntry.is_dir() and dirEntry.name not in ['Plex Versions']


def getAllImageFilesInHierarchy(path):
    """
    Returns a list of file paths relative to 'path' for all images under the given directory,
    recursively looking in subdirectories
    """
    return [f for f in scan_tree(path)]


def scan_tree(path, prePath=None):
    """Recursively yield file names for given directory."""
    for entry in os.scandir(path):
        entryPath = os.path.join(prePath, entry.name) if prePath is not None else entry.name

        if entry.is_dir(follow_symlinks=False):
            yield from scan_tree(entry.path, entryPath)
        else:
            if shouldReturnFile(entry, ['png', 'jpg', 'jpeg']):
                yield entryPath


def shouldReturnFile(dirEntry, onlyMatchExt=None):
    if onlyMatchExt is None:
        return dirEntry.is_file()
    else:
        return dirEntry.is_file() and os.path.splitext(dirEntry.name)[1][1:] in onlyMatchExt


def getMetadataFilename(filePath):
    return os.path.splitext(filePath)[0] + '.metadata'


def getPlexAssociatedFiles(filePath):
    """Returns all files with the same base name as the given file path"""
    (fileBase, fileExt) = os.path.splitext(filePath)
    return glob.iglob(fileBase + ".*")


def getResourceFilePath(resourceRelativeFilePath):
    moduleDir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(moduleDir, 'resources', resourceRelativeFilePath))
