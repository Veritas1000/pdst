import collections
import logging
import os
import re
from enum import Enum, auto

import simplejson as json
from fuzzywuzzy import fuzz

from pdst.db.PlexDao import PlexDao
from pdst.parsing import convertSpacesToRegex

log = logging.getLogger(__name__)


class Config:

    def __init__(self, configFile):
        self.rawConfig = None

        if configFile is not None:
            with open(configFile) as f:
                self.rawConfig = json.load(f)

        self.sports = []
        for entry in self.__getConfigOrDefault('sports', []):
            self.sports.append(SportConfigEntry(entry))

        self.imageRoot = self.__getConfigOrDefault('imageRoot', None)

        self.thumbnailSize = self.__getConfigOrDefault('thumbnailSize', [800, 450])
        self.fallbackColor = self.__getConfigOrDefault('fallbackColor', '#ccc').replace('#', '')

        self.videoExtensions = self.__getConfigOrDefault('videoExtensions', ['mkv', 'ts', 'mp4'])
        self.imageExtensions = self.__getConfigOrDefault('imageExtensions', ['png', 'jpg', 'jpeg'])
        self.createdImageExtension = self.__getConfigOrDefault('createdImageExtension', 'png')

        self.plexLibPath = self.__getConfigOrDefault('plexLibrary', None)
        if self.plexLibPath is None:
            log.warning(f"Plex Library is not configured! any metadata operations will fail!")
        self.plexDao = PlexDao(self.plexLibPath)

        self.moveTarget = self.__getConfigOrDefault('moveTarget', os.getcwd())
        umaskStr = self.__getConfigOrDefault('umask', '022')
        self.umask = int(umaskStr, 8)
        os.umask(self.umask)

    def __getConfigOrDefault(self, configKey, default):
        if self.rawConfig is not None and configKey in self.rawConfig:
            return self.rawConfig[configKey]
        else:
            return default


class DateOverrideMode(Enum):
    NEVER = auto()
    ALWAYS = auto()
    EOY = auto()

    @staticmethod
    def fromString(string):
        return {
            'never': DateOverrideMode.NEVER,
            'always': DateOverrideMode.ALWAYS,
            'eoy': DateOverrideMode.EOY
        }.get(string.lower(), None)


class SportConfigEntry:

    def __init__(self, sportEntry):
        self.name = sportEntry['name']
        self.imageRoot = sportEntry['imageRoot'] if 'imageRoot' in sportEntry else None
        self.image = sportEntry['image'] if 'image' in sportEntry else None
        self.logo = sportEntry['logo'] if 'logo' in sportEntry else None
        self.rawMatches = sportEntry['matches'] if 'matches' in sportEntry else []
        self.dateOverride = DateOverrideMode.fromString(sportEntry['dateOverride']) if 'dateOverride' in sportEntry \
            else DateOverrideMode.EOY

        self.overrideShow = sportEntry['overrideShow'] if 'overrideShow' in sportEntry else False

        self.imageTextRegex = sportEntry['imageTextRegex'] if 'imageTextRegex' in sportEntry else None
        self.background = sportEntry['background'] if 'background' in sportEntry else None

        self.__processMatches()

    def __processMatches(self):
        """Process the ingested matches to add whitespace/separator handling regexes"""
        processed = []

        for matchEntry in self.rawMatches:
            processed.append(SportMatchEntry(matchEntry))

        self.matches = processed

    def matchFor(self, searchStr):
        log.debug(f"[{self.name}] Trying to get a match for {searchStr}")
        bestMatch = None
        bestScore = 0

        if len(self.matches) == 0:
            bestMatch = self.name
            bestScore = fuzz.partial_ratio(searchStr, self.name)

        else:
            for matchCandidate in self.matches:
                match, score = matchCandidate.getMatchScore(searchStr)

                if score > bestScore:
                    bestScore = score
                    bestMatch = match

        log.debug(f"Best we could find was ({bestMatch}, {bestScore})")
        return bestMatch, bestScore

    def matchObjectFor(self, searchStr):
        log.debug(f"Trying to get match object for {searchStr}")
        bestMatchEntry = None
        bestScore = 0

        if len(self.matches) == 0:
            bestMatchEntry = SportMatchEntry(self.name)
            bestScore = fuzz.partial_ratio(searchStr, self.name)

        else:
            for matchCandidate in self.matches:
                match, score = matchCandidate.getMatchScore(searchStr)

                if score > bestScore:
                    bestScore = score
                    bestMatchEntry = matchCandidate

        log.debug(f"Best we could find was ({bestMatchEntry}, {bestScore})")
        return bestMatchEntry, bestScore

    def getImageTextFor(self, metadata):
        text = None
        if metadata is not None and self.imageTextRegex is not None:
            log.debug(f"Getting image text for {metadata.title}")
            match = re.match(self.imageTextRegex, metadata.title)
            if match is not None:
                text = match.groups()[-1]

        return text

    def getDefaultImage(self):
        if self.image is None:
            return self.logo
        else:
            return self.image

    def __str__(self):
        return f"[SportConfigEntry: name={self.name}, imageRoot={self.imageRoot}, matches={self.matches}]"


class SportMatchEntry:

    def __init__(self, configEntry):
        self.matchRegex = None
        self.overrideShow = False

        p = re.compile(r"\s+", re.IGNORECASE)

        if isinstance(configEntry, collections.abc.Mapping):
            if 'match' in configEntry:
                self.matchRegex = convertSpacesToRegex(configEntry['match'])

            if 'rawRegex' in configEntry:
                self.matchRegex = configEntry['rawRegex']

            if 'overrideShow' in configEntry:
                self.overrideShow = configEntry['overrideShow'] or False

        else:
            self.matchRegex = convertSpacesToRegex(configEntry)

    def getMatchScore(self, matchAgainst):
        score = 0
        matchStr = None

        match = re.search(rf"{self.matchRegex}", matchAgainst, re.IGNORECASE)
        log.debug(f"regex matched {match} from {self.matchRegex}")
        if match is not None:
            matchStr = match[0]
            score = fuzz.partial_ratio(matchAgainst, matchStr)
            log.debug(f" ^ scored {score}")

        return matchStr, score
