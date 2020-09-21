import logging
import os
import re
from datetime import timedelta

from pdst.sports import TeamSpec

log = logging.getLogger(__name__)

DELIMITER_MATCH = r"[\s\.\-_]"
COLOR_HEX_MATCH = r"(?:[a-f0-9]{3}){1,2}"
BG_PATTERN_MATCH = r"bg\$([0-9a-z.]+)"
MASK_MATCH = rf"mask\$({COLOR_HEX_MATCH})"
STROKE_MATCH = rf"stroke\$(\d+)\$({COLOR_HEX_MATCH})"
DELIM_HINT_MATCH = rf"{DELIMITER_MATCH}(?:{COLOR_HEX_MATCH}i?|{BG_PATTERN_MATCH}|{MASK_MATCH}|{STROKE_MATCH})"


def removeBadFilenameChars(original):
    """Removes illegal filename characters"""
    return re.sub(r'[:/\\?%*\[\]|"\'<>]', '', original)


def removeYears(original):
    """Removes any (assumed) years from original that may be of the form (YYYY) or YYYY"""
    if original is None:
        return None

    subbed = re.sub(r'\s*\(?\d{4}\)?\s*', '', original)
    return subbed.strip()


def teamNamesFromMatch(text):
    """Find and return likely team names from the match title

    Searches text for likely team names, assuming the input string is of the form:
    [something] [at|vs.?] [something]

    potential word delimiters: ' ', '.', '_', '-'

    TODO: multi-lang support
    """
    log.debug(f"Looking for team names in '{text}'")

    # first look JUST for vs/at to prevent catastrophic backtracking in the bigger regex
    pre = re.compile(rf"(?:{DELIMITER_MATCH}(?:vs\.?|at){DELIMITER_MATCH})", re.IGNORECASE)
    if not pre.search(text):
        return None

    pattern = re.compile(rf"""
        ((?:\w+{DELIMITER_MATCH}?)+)    # First team name including delimeters
        (?:{DELIMITER_MATCH}(?:vs\.?|at){DELIMITER_MATCH})
        ((?:\w+{DELIMITER_MATCH}?)+)     # Second team name including delimeters
        """, re.VERBOSE | re.IGNORECASE)

    match = pattern.search(text)

    log.debug(match)

    return match


def cleanImageHints(imagePath):
    """Removes any trailing image hints such as color, BG pattern, etc"""
    log.debug(f"Extracting team name from '{imagePath}'")

    pattern = re.compile(rf"""
        (.+?)
        (?:{DELIM_HINT_MATCH})*
        (?:\.\w+)$
        """, re.VERBOSE | re.IGNORECASE)

    base = os.path.basename(imagePath)
    match = pattern.match(base)
    teamName = match.group(1)
    log.debug(f"Assumed team name: '{teamName}'")

    return teamName


def hasHints(path):
    """Returns True if the image path has one or more hex color codes in its image hints, False otherwise"""
    log.debug(f"Testing if there is a trailing color code in '{path}'")

    pattern = re.compile(rf"""
        (.+?)
        ({DELIM_HINT_MATCH})+
        (\.\w+)$
        """, re.VERBOSE | re.IGNORECASE)

    base = os.path.basename(path)
    match = pattern.match(base)
    return match is not None


def getColorFromFilename(path, position=0):
    """Pull out the embedded hex color code from the given filename.

    If there is more than one, you can pull out specific colors using the equivalent index,
    if the filename colors were a List (0-indexed, left to right).

    If there are no colors found, None is returned

    If there is at least one color found, and an index *greater than* the number of colors,
    the last color is returned
    """
    log.debug(f"Pulling color #{position + 1} from '{path}'")

    colorMatches = getAllColorsFromFilename(path)

    if colorMatches is None:
        return None

    if position >= len(colorMatches):
        position = len(colorMatches) - 1

    return colorMatches[position]


def getAllColorsFromFilename(path):
    """Returns a list of all color hints found in the file name, or None if none found"""

    log.debug(f"Pulling all color hints from '{path}'")

    pattern = re.compile(rf"""
        (?:.+?)
        ((?:{DELIM_HINT_MATCH})+)
        (?:\.\w+)$
        """, re.VERBOSE | re.IGNORECASE)

    match = pattern.match(path)
    if match is None:
        return None

    allHints = match.group(1)

    pattern2 = re.compile(r"""
        (?:[\s.\-_]((?:[a-f0-9]{3}){1,2}))
        """, re.VERBOSE | re.IGNORECASE)

    colorMatches = pattern2.findall(allHints)
    return colorMatches


def setColorInFilename(file, colorHex, invert=False):
    """Set the trailing color code in the given filename.

    If there are any existing trailing color codes, they will be removed and replaced by the given color code
    """
    pattern = re.compile(rf"""
        (.+?)                       # filename base
        (?:(?:{DELIMITER_MATCH}{COLOR_HEX_MATCH}i?)*?)    # any trailing color codes _which will be removed_
        (\.\w+)$                    # extension
        """, re.VERBOSE | re.IGNORECASE)

    dirname = os.path.dirname(file)
    base = os.path.basename(file)

    match = pattern.match(base)

    newFile = match[1] + '_' + colorHex

    if invert:
        newFile += 'i'

    newFile += match[2]

    fullPath = os.path.join(dirname, newFile)

    return fullPath


def isColorInverted(path, position=0):
    """Returns True if the color at the given position in the filename is flagged to invert"""
    pattern = re.compile(rf"""
        (?:.+?)
        ((?:{DELIM_HINT_MATCH})+)
        (?:\.\w+)$
        """, re.VERBOSE | re.IGNORECASE)

    match = pattern.match(path)
    if match is None:
        return None

    allHints = match.group(1)

    pattern2 = re.compile(r"""
        ((?:[a-f0-9]{3}){1,2}i?)
        """, re.VERBOSE | re.IGNORECASE)

    colorMatches = pattern2.findall(allHints)

    if position >= len(colorMatches):
        position = len(colorMatches) - 1

    return colorMatches[position].endswith(('i', 'I'))


def removePlexShowYear(title):
    """Removes any trailing year specification of the form '(YYYY)' as is often found in Plex show names"""
    return re.sub(r'([\s.\-_]\(\d{4}\))$', '', title)


def teamNamesFromFilename(filename):
    # TODO make this delimiter configurable! or make more flexible?
    fileParts = os.path.splitext(filename)[0].split(' - ')

    log.debug(fileParts)

    team1 = None
    team2 = None
    for token in fileParts:
        match = teamNamesFromMatch(token)
        if match:
            team1 = match.group(1)
            team2 = match.group(2)
            break

    return team1, team2


def titleFromFilename(filename):
    fileParts = os.path.splitext(filename)[0].split(' - ')
    if len(fileParts) > 2:
        return fileParts[-1]


def getBgPatternHint(filename):
    """Parses out a background pattern hint from the filename"""

    pattern = re.compile(rf"(?:{DELIMITER_MATCH}{BG_PATTERN_MATCH}{DELIMITER_MATCH})", re.IGNORECASE)

    match = pattern.search(filename)

    if match is None:
        return None

    return match[1]


def getMaskHint(filename):
    """Parses out a mask hint from the filename"""
    pattern = re.compile(rf"(?:{DELIMITER_MATCH}{MASK_MATCH}{DELIMITER_MATCH})", re.IGNORECASE)
    match = pattern.search(filename)

    if match is None:
        return None

    return match[1]


def getStrokeHint(filename):
    """Parses out a mask hint from the filename"""
    pattern = re.compile(rf"(?:{DELIMITER_MATCH}{STROKE_MATCH}{DELIMITER_MATCH})", re.IGNORECASE)
    match = pattern.search(filename)

    if match is None:
        return None, None

    return int(match[1]), match[2]


def isTeamsString(inStr):
    return re.match(r'teams?:', inStr, re.IGNORECASE) is not None


def parseTeamsString(inStr):
    """Returns the list of team specs from an input string of the forms:
        teams:Sport1/Team 1--Sport 2/Team 2
        team:Sport 1/Team 1
    """
    pattern = re.compile(r'teams?:(.+)', re.IGNORECASE)
    match = pattern.match(inStr)

    if match is None:
        return None

    teamsSplit = match[1].split('--')
    teams = [None, None]
    for i in range(0, 2):
        if len(teamsSplit) > i:
            group = teamsSplit[i]
            if group is not None and group != '':
                sport = None
                split = group.split('/')
                if len(split) == 1:
                    team = split[0]
                else:
                    sport = split[0]
                    team = split[1]
                teams[i] = TeamSpec(team, sport)

    nonNone = [t for t in teams if t is not None]

    onlySport = None
    for spec in nonNone:
        if spec.sportName is not None:
            if onlySport is not None:
                if spec.sportName != onlySport:
                    onlySport = None
                    break
            else:
                onlySport = spec.sportName

    if onlySport is not None:
        for spec in nonNone:
            spec.sportName = onlySport

    return nonNone


def convertSpacesToRegex(source):
    p = re.compile(r"\s+", re.IGNORECASE)
    return re.sub(p, r"[\\s\\.\\-_]+", source.strip())


def parseTimedelta(inStr):
    if inStr is None:
        return None

    pattern = re.compile(r"(\d+)([wdh])", re.IGNORECASE)
    matches = re.findall(pattern, inStr)

    hours = 0
    days = 0
    weeks = 0

    for match in matches:
        n = int(match[0])
        spec = match[1]
        if spec == 'h':
            hours += n
        elif spec == 'd':
            days += n
        elif spec == 'w':
            weeks += n

    if hours + days + weeks < 1:
        return None

    return timedelta(days=days, hours=hours, weeks=weeks)
