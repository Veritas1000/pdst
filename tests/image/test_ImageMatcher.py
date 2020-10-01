import os
import unittest
from unittest.mock import patch

from parameterized import parameterized

from pdst.image.ImageMatcher import ImageMatcher


def returnMLSImages(*args):
    return ['Atlanta_United_231f20.png', 'LAFC_17191d.png', 'Philadelphia_Union_071b2c.png',
            'Chicago_Fire_06134d.png', 'LA_Galaxy_0f2351.png', 'Portland_Timbers_0d421d.png',
            'Colorado_Rapids_960a2c.png', 'Minnesota_United_231f20.png', 'Real_Salt_Lake_013a81.png',
            'Columbus_Crew_fef101.png', 'Montreal_Impact_224479.png', 'San_Jose_Earthquakes_0066af.png',
            'DC_United_231f20.png', 'Seattle_Sounders_5d9741.png',
            'FC_Cincinnati_263b80.png', 'New_England_Revolution_002b5c.png', 'Sporting_Kansas_City_002f65.png',
            'FC_Dallas_2a4076.png', 'New_York_City_FC_78a5db.png', 'Toronto_FC_e31937.png',
            'Houston_Dynamo_e67425.png', 'New_York_Red_Bulls_23326a.png', 'Vancouver_Whitecaps_00245e.png',
            'Inter_Miami_f1b1c9.png', 'Orlando_City_633492.png']


class TestImageMatcher(unittest.TestCase):

    def setUp(self):
        self.matcher = ImageMatcher('/fakeRoot')

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findMatchingImageDirs_both_found(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['MLS.Soccer', 'Super.Rugby', 'NFL.Football'],  # top level dirs
            ['Season.2020', 'Season 2019'],  # second level dirs
        ]

        (sportDir, seasonDir) = self.matcher.findMatchingImageDirs('Season 2020', 'MLS Soccer (2009)')

        self.assertEqual('MLS.Soccer', sportDir)
        self.assertEqual('Season.2020', seasonDir)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findMatchingImageDirs_no_season(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['MLS.Soccer', 'Super.Rugby', 'NFL.Football'],  # top level dirs
            ['Season 2019'],
        ]

        (sportDir, seasonDir) = self.matcher.findMatchingImageDirs('Season 2020', 'MLS Soccer (2009)')

        self.assertEqual('MLS.Soccer', sportDir)
        self.assertEqual(None, seasonDir)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findMatchingImageDirs_no_seasons(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['MLS.Soccer', 'Super.Rugby', 'NFL.Football'],  # top level dirs
            [],
        ]

        (sportDir, seasonDir) = self.matcher.findMatchingImageDirs('Season 2020', 'MLS Soccer (2009)')

        self.assertEqual('MLS.Soccer', sportDir)
        self.assertEqual(None, seasonDir)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findMatchingImageDirs_no_dirs(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            [],
        ]

        (sportDir, seasonDir) = self.matcher.findMatchingImageDirs('Season 2020', 'MLS Soccer (2009)')

        self.assertEqual(None, sportDir)
        self.assertEqual(None, seasonDir)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findMatchingImageDirs_none(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['MLS.Soccer', 'Super.Rugby', 'NFL.Football'],  # top level dirs
        ]

        (sportDir, seasonDir) = self.matcher.findMatchingImageDirs('Season 2018', '2018 FIFA World Cup Russia (2014)')

        self.assertEqual(None, sportDir)
        self.assertEqual(None, seasonDir)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findBestMatch_sport_season(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['MLS.Soccer', 'Super.Rugby', 'NFL.Football'],  # top level dirs
            ['Season 2019', 'Season.2020'],  # season level dirs
        ]

        mock_filetools.getImageFilesInDir.side_effect = [
            ['LAFC_Los_Angeles_FC_faf123.png', 'Los_Angeles_Galaxy_000.png', 'Orlando.City.123456.png'],
            # sport dir images
            ['LAFC_Los_Angeles_FC_ffb432.png', 'Chicago_Fire_abc.png'],  # season dir images
        ]

        logo = self.matcher.findBestMatch('Los Angeles FC', 'Season 2020', 'MLS Soccer')

        expected = os.path.join('/fakeRoot', 'MLS.Soccer', 'Season.2020', 'LAFC_Los_Angeles_FC_ffb432.png')
        self.assertEqual(expected, logo)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findBestMatch_sport_only(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['MLS.Soccer', 'Super.Rugby', 'NFL.Football'],  # top level dirs
            [],  # season level dirs
        ]

        mock_filetools.getImageFilesInDir.side_effect = [
            ['LAFC_Los_Angeles_FC_faf123.png', 'Los_Angeles_Galaxy_000.png', 'Orlando.City.123456.png'],
            # sport dir images
        ]

        logo = self.matcher.findBestMatch('LAFC', 'Season 2020', 'MLS Soccer')

        expected = os.path.join('/fakeRoot', 'MLS.Soccer', 'LAFC_Los_Angeles_FC_faf123.png')
        self.assertEqual(expected, logo)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findBestMatch_clean_hints(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['Sport'],  # top level dirs
            [],  # season level dirs
        ]

        mock_filetools.getImageFilesInDir.return_value = ['Alpha_FC_abc123.png', 'Another.City.fafc12.png']

        logo = self.matcher.findBestMatch('AFC', 'Sport')
        expected = os.path.join('/fakeRoot', 'Sport', 'Alpha_FC_abc123.png')
        self.assertEqual(expected, logo)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findBestMatch_multiple_teams(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['NFL.Football'],  # top level dirs
            [],  # season level dirs
        ]

        mock_filetools.getImageFilesInDir.side_effect = [
            ['Los_Angeles_Rams_faf123.png', 'Los_Angeles_Chargers_000.png', 'Chicago.Bears.123456.png'],
            # sport dir images
        ]

        logo = self.matcher.findBestMatch('LA Rams', 'Season 2020', 'NFL Football (2020)')
        expected = os.path.join('/fakeRoot', 'NFL.Football', 'Los_Angeles_Rams_faf123.png')
        self.assertEqual(expected, logo)

    @patch('pdst.image.ImageMatcher.filetools')
    def test_findBestMatch_none_good(self, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['NFL.Football'],  # top level dirs
            [],  # season level dirs
        ]

        mock_filetools.getImageFilesInDir.side_effect = [
            ['Los_Angeles_Rams_faf123.png', 'Green_Bay_Packers_000.png', 'Chicago.Bears.123456.png'],
            # sport dir images
        ]

        logo = self.matcher.findBestMatch('Tampa Bay Buccaneers', 'Season 2020', 'NFL Football (2020)')
        self.assertEqual(None, logo)

    @parameterized.expand([
        (['Test.png'], 'Test', 'Test.png'),

        (['Florida_Atlantic_FAU_Owls.png', 'Florida_Gators.png', 'Florida_State_Seminoles.png'],
            'Florida', 'Florida_Gators.png'),

        (['Florida_Atlantic_FAU_Owls.png', 'Florida_Gators.png', 'Florida_State_Seminoles.png'],
            'Florida State', 'Florida_State_Seminoles.png'),

        (['Florida_Atlantic_FAU_Owls.png', 'Florida_Gators.png', 'Florida_State_Seminoles.png'],
            'FSU Seminoles', 'Florida_State_Seminoles.png'),

        (['Florida_Atlantic_FAU_Owls.png', 'Florida_Gators.png', 'Florida_State_Seminoles.png'],
            'FAU Owls', 'Florida_Atlantic_FAU_Owls.png'),
    ])
    @patch('pdst.image.ImageMatcher.filetools')
    def test_findBestMatch_multiple_teams(self, logos, searchName, expectedImg, mock_filetools):
        mock_filetools.getSubdirs.side_effect = [
            ['Sport'],  # top level dirs
            [],  # season level dirs
        ]
        mock_filetools.getImageFilesInDir.return_value = logos

        logo = self.matcher.findBestMatch(searchName, 'Season', 'Sport')
        expected = os.path.join('/fakeRoot', 'Sport', expectedImg)
        self.assertEqual(expected, logo)
