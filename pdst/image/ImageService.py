import logging
import os

from pdst import parsing
from pdst.Config import Config
from pdst.MetadataService import MetadataService
from pdst.SportService import SportService
from pdst.db.PlexDao import PlexDao
from pdst.image import ImageGenerationException
from pdst.image.ImageGenerator import ImageGenerator
from pdst.image.ImageMatcher import ImageMatcher
from pdst.image.spec import ImageSpec, CompositeSpec
from pdst.util import removeNones

log = logging.getLogger(__name__)


class ImageService:

    def __init__(self, config, imageGen=None, sportService=None, metadataService=None):
        if config is None:
            config = Config(None)

        self.config = config
        self.imageGen = ImageGenerator(config) if imageGen is None else imageGen
        self.sportService = SportService(config) if sportService is None else sportService

        self.metadataService = MetadataService(PlexDao(config.plexLibPath), self.sportService) \
            if metadataService is None \
            else metadataService

    def generateEventThumbnail(self, filePath):
        log.debug(f"Generating thumbnail image for {filePath}")

        imageSpecs = self.getImageSpecsForFilename(filePath)
        if imageSpecs is None or len(imageSpecs) == 0:
            raise ImageGenerationException(f'No logos found for {filePath}')

        compositeSpec = self.__getCompositeSpec(filePath)
        return self.imageGen.generateImage(compositeSpec, imageSpecs)

    def getMatchingImageName(self, inFile):
        return os.path.splitext(inFile)[0] + '.' + self.config.createdImageExtension

    def generateImage(self, imageDimensions, teamSpecs, imageSpecOverride=None, text=None):
        log.debug(f"Generating {imageDimensions[0]}x{imageDimensions[1]} image for {teamSpecs}")

        # TODO: push up, have passed in?
        compositeSpec = CompositeSpec(imageDimensions, text)

        imageSpecs = self.getImageSpecs(teamSpecs, imageSpecOverride)
        foundImages = removeNones(imageSpecs)
        numFound = len(foundImages)
        if numFound == 0:
            log.warning(f"Did not get ANY image specs from {teamSpecs}")
            return None
        elif numFound in [1, 2]:
            return self.imageGen.generateImage(compositeSpec, foundImages)
        else:
            raise ImageGenerationException(f"Don't know how to generate an image for {numFound} teams")

    def getImageSpecs(self, teamSpecs, imageSpecOverride=None):
        """Returns a list of ImageSpecs corresponding to each given TeamSpec"""
        result = []

        for teamSpec in teamSpecs:
            sportEntry = self.sportService.getSportFor(teamSpec.sportName)
            if sportEntry is None:
                log.warning(f"Unable to find a matching Sport entry for {teamSpec.sportName}!")

            else:
                spec = self.__imageSpecFor(sportEntry, teamSpec.teamName)
                spec.override(imageSpecOverride)
                result.append(spec)

        return result

    def __imageSpecFor(self, sportEntry, teamName):
        imageSpec = None
        if sportEntry is not None:
            if sportEntry.image is not None:
                imageSpec = ImageSpec(sportEntry.image, False)

            if sportEntry.imageRoot is None:
                if sportEntry.image is None:
                    log.debug(f"Sport {sportEntry.name} has no configured image or imageRoot")
            else:
                matcher = ImageMatcher(sportEntry.imageRoot)
                image = matcher.findBestMatch(teamName, sportEntry.name)
                if image is None:
                    log.debug(f"No image match found for {teamName}")
                else:
                    imageSpec = ImageSpec(image)

            if sportEntry.background is not None:
                imageSpec.bg = sportEntry.background

        return imageSpec

    def getImageSpecsForFilename(self, filePath):
        log.debug(f"Getting image specs for {filePath}")

        sportEntry = self.sportService.getSportFor(filePath)

        if sportEntry is None:
            raise ImageGenerationException(f"Unable to find a matching Sport entry for {filePath}!")

        filename = os.path.split(filePath)[1]
        (team1, team2) = parsing.teamNamesFromFilename(filename)
        teamNames = removeNones([team1, team2])
        result = []

        for team in teamNames:
            teamSpec = self.__imageSpecFor(sportEntry, team)
            if teamSpec is not None:
                result.append(teamSpec)

        if len(result) == 0:
            title = parsing.titleFromFilename(filePath)
            if title is not None:
                imageSpec = self.__imageSpecFor(sportEntry, title)
                if imageSpec is not None:
                    imageSpec.isLogo = False
                    result.append(imageSpec)

        if len(result) == 0:
            if sportEntry.image is not None:
                imageSpec = ImageSpec(sportEntry.image, False)
                result.append(imageSpec)
            elif sportEntry.logo is not None:
                imageSpec = ImageSpec(sportEntry.logo, True)
                result.append(imageSpec)
            else:
                raise ImageGenerationException(f"Unable to get any image specs for {filePath}!")

        return result

    def __getCompositeSpec(self, filePath):
        log.debug(f"Getting composite spec for {filePath}")
        dimensions = self.config.thumbnailSize
        text = None

        metadata = self.metadataService.getMetadataForEpisodeFile(filePath)
        sportEntry = self.sportService.getSportFor(filePath)
        if metadata is not None and sportEntry is not None:
            text = sportEntry.getImageTextFor(metadata)

        return CompositeSpec(dimensions, text)
