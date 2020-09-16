import logging
import os

from fuzzywuzzy import process, fuzz

from pdst import parsing, filetools

log = logging.getLogger(__name__)


class ImageMatcher:
    GOOD_IMAGE_MATCH_THRESHOLD = 50  # TODO: make this configurable!
    GOOD_MATCH_THRESHOLD = 60  # TODO: make this configurable!
    GREAT_MATCH_THRESHOLD = 85  # TODO: make this configurable!

    def __init__(self, rootDir):
        log.debug(f"ImageMatcher root image dir is {rootDir}")
        self.rootDir = rootDir

    def findMatchingImageDirs(self, refParentDir, refGrandparentDir):
        """Tries to find corresponding image directories in the image tree to match the given parent and 
        grandparent dirs (which would generally be from a video file we want to get logos for)
        """
        log.debug(f"Searching for matching image dirs to match {refParentDir} and {refGrandparentDir}")

        topLevelDirs = filetools.getSubdirs(self.rootDir)

        if topLevelDirs is None or len(topLevelDirs) == 0:
            return (None, None)

        pMatch = process.extractOne(refParentDir, topLevelDirs)

        gpMatch = (None, 0)
        if refGrandparentDir is not None:
            gpMatch = process.extractOne(refGrandparentDir, topLevelDirs)

        log.debug(f"Best top level match for {refGrandparentDir}: {gpMatch}")
        log.debug(f"Best top level match for {refParentDir}: {pMatch}")

        sportDir = None
        seasonDir = None

        if gpMatch[1] > pMatch[1] and self.__isGoodMatch(gpMatch):
            # refGrandparentDir is probably sport, look for refParentDir match in its subdirectories
            sportDir = gpMatch[0]
            secondLevelDirs = filetools.getSubdirs(os.path.join(self.rootDir, sportDir))

            if secondLevelDirs is not None and len(secondLevelDirs) > 0:
                bestSecondMatch = process.extractOne(refParentDir, secondLevelDirs)
                log.debug(f"Best second level match for {refParentDir}: {bestSecondMatch}")
                seasonDir = bestSecondMatch[0] if self.__isGreatMatch(bestSecondMatch) else None

        else:
            # refParentDir is probably sport, can probably ignore refGrandparentDir and we don't know season (or there is none)
            sportDir = pMatch[0] if self.__isGoodMatch(pMatch) else None

        log.debug(f"Returning (sportDir = {sportDir}, seasonDir = {seasonDir})")
        return sportDir, seasonDir

    def __isGoodMatch(self, match):
        return match is not None and match[1] > ImageMatcher.GOOD_MATCH_THRESHOLD

    def __isGreatMatch(self, match):
        return match is not None and match[1] > ImageMatcher.GREAT_MATCH_THRESHOLD

    def __matchAtLeast(self, match, threshold):
        return match is not None and match[1] > threshold

    def findBestMatch(self, team, refParentDir=None, refGrandparentDir=None):
        log.debug(
            f"Searching for best match for Team {team}, with reference dirs {refParentDir} and {refGrandparentDir}")

        (sportDir, seasonDir) = self.findMatchingImageDirs(refParentDir, refGrandparentDir)

        return self.__findBestImageMatch(team, sportDir, seasonDir)

    def findBestMatches(self, team1, team2, refParentDir=None, refGrandparentDir=None):
        log.debug(
            f"Searching for best matches for Teams {team1} and {team2}, with reference dirs {refParentDir} and {refGrandparentDir}")

        (sportDir, seasonDir) = self.findMatchingImageDirs(refParentDir, refGrandparentDir)

        logo1 = self.__findBestImageMatch(team1, sportDir, seasonDir)
        if logo1 is None:
            log.debug(f"No good logo found for {team1} in the reference dirs.")

        logo2 = self.__findBestImageMatch(team2, sportDir, seasonDir)
        if logo2 is None:
            log.debug(f"No good logo found for {team2} in the reference dirs.")

        return (logo1, logo2)

    def __findBestImageMatch(self, team, sportDir, seasonDir):
        log.debug(f"Looking for logo for {team} in image dirs {sportDir}/{seasonDir}")

        bestMatch = None
        if sportDir:
            fullSportDir = os.path.join(self.rootDir, sportDir)
            sportsDirImages = filetools.getImageFilesInDir(fullSportDir)

            sportDirMatch = self.__extractImageMatch(team, sportsDirImages)
            log.debug(f"Sport Dir Match: {sportDirMatch}")

            if self.__matchAtLeast(sportDirMatch, self.GOOD_IMAGE_MATCH_THRESHOLD):
                bestMatch = os.path.join(fullSportDir, sportDirMatch[0])

            if seasonDir is not None:
                fullSeasonDir = os.path.join(fullSportDir, seasonDir)
                seasonDirImages = filetools.getImageFilesInDir(fullSeasonDir)

                seasonDirMatch = self.__extractImageMatch(team, seasonDirImages)
                log.debug(f"Season Dir Match: {seasonDirMatch}")

                if seasonDirMatch[1] >= sportDirMatch[1] and self.__matchAtLeast(seasonDirMatch,
                                                                                 self.GOOD_IMAGE_MATCH_THRESHOLD):
                    bestMatch = os.path.join(fullSeasonDir, seasonDirMatch[0])

        if bestMatch is None:  # TODO: This needs improvement
            allImages = filetools.getAllImageFilesInHierarchy(self.rootDir)
            allImagesMatch = self.__extractImageMatch(team, allImages)
            log.debug(f"Best *all* images match: {allImagesMatch}")
            if self.__matchAtLeast(allImagesMatch, self.GOOD_IMAGE_MATCH_THRESHOLD):
                bestMatch = os.path.join(self.rootDir, allImagesMatch[0])

        log.debug(f"Best (acceptable) logo match for {team} seems to be {bestMatch}")
        return bestMatch

    def __extractImageMatch(self, searchTarget, images):
        bestMatch = None
        bestScore = 0
        for dirtyFilename in images:
            cleaned = parsing.cleanImageHints(dirtyFilename)
            score = fuzz.partial_ratio(searchTarget, cleaned)
            if score > bestScore:
                bestScore = score
                bestMatch = dirtyFilename

        return bestMatch, bestScore

    def getLogo(self, teamSpec):
        return self.findBestMatch(teamSpec.teamName, teamSpec.sportName)