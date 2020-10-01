import os
import unittest
from unittest.mock import patch

from pdst.Config import Config
from pdst.image.ImageService import ImageService, ImageGenerationException


class TestImageService(unittest.TestCase):

    def setUp(self):
        testsDir = os.path.normpath(os.path.join(os.path.split(__file__)[0], '..'))
        jsonPath = os.path.join(testsDir, 'test-files', 'test_ImageService_sports.json')
        self.config = Config(jsonPath)
        self.service = ImageService(self.config)

    def test_generateThumbnail_no_sport(self):
        self.assertRaises(ImageGenerationException,
                          self.service.generateEventThumbnail,
                          '/no/matching/sport/eg/Cricket/Team One vs Team 2.mp4')

    def test_generateThumbnail_no_sport_image_cfgs(self):
        self.assertRaises(ImageGenerationException,
                          self.service.generateEventThumbnail,
                          '/matches/an/Incomplete.Sport.Def/event.mkv')

    @patch('pdst.image.ImageService.ImageMatcher')
    def test_generateThumbnail_no_team_matches_no_sport_img(self, mockIm):
        mockIm.return_value.findBestMatch.return_value = None

        self.assertRaises(ImageGenerationException,
                          self.service.generateEventThumbnail,
                          '/matches/no_teams/team a vs team b.mkv')

    def test_getImageSpecsForFilename_noTeams_sportImg(self):

        imageSpecs = self.service.getImageSpecsForFilename('/Just.Image/Test Sport - 2020-02-02 - Event Title.mkv')

        self.assertIsNotNone(imageSpecs)
        self.assertEqual(1, len(imageSpecs))

        self.assertEqual('/just/sport/image.png', imageSpecs[0].imageFile)
        self.assertEqual(False, imageSpecs[0].isLogo)

    @patch('pdst.image.spec.util.getColorsForImage')
    def test_getImageSpecsForFilename_noTeams_sportLogo(self, mockGetColors):
        mockGetColors.return_value = []
        imageSpecs = self.service.getImageSpecsForFilename('/Just.Logo/Test Sport - 2020-02-02 - Event Title.mkv')

        self.assertIsNotNone(imageSpecs)
        self.assertEqual(1, len(imageSpecs))

        self.assertEqual('/just/sport/logo.png', imageSpecs[0].imageFile)
        self.assertEqual(True, imageSpecs[0].isLogo)
