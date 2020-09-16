import os
import unittest

from parameterized import parameterized

from pdst.Config import Config
from pdst.SportService import SportService


class TestSportService(unittest.TestCase):

    def setUp(self):
        testsDir = os.path.split(__file__)[0]
        jsonPath = os.path.join(testsDir, 'test-files', 'test_sports.json')
        self.service = SportService(Config(jsonPath))

    def test_init_noConfig(self):
        service = SportService(None)
        self.assertEqual([], service.sports)

    def test_init_valid(self):
        self.assertIsNotNone(self.service.sports)

    @parameterized.expand([
        ('/data/Classic College Football (2019)/Season 2019/Classic College Football (2019) - 2019-12-07 07 00 00 - 2019 Georgia vs. LSU.ts',
        'NCAA'),
        ('/data/2018 FIFA World Cup Russia (2014)/Season 2018/2018 FIFA World Cup Russia (2014) - 2018-07-10 08 00 00 - France vs. Belgium.ts',
        'International'),
        ('/data/media/video/sports-test/Formula One Racing (2019)/Season 2020/Formula One Racing (2019) - 2020-08-02 08 00 00 - British Grand Prix.ts',
        'Formula 1'),
    ])
    def test_getSportFor_basic(self, path, expected):
        sportEntry = self.service.getSportFor(path)
        self.assertEqual(expected, sportEntry.name)

    @parameterized.expand([
        ('/data/NCAA.Football/Georgia.vs.LSU.ts', 'NCAA'),
        ('/data/College-Basketball/Florida.vs.Kentucky.ts', 'NCAA'),
        ('/data/Formula__1/British Grand Prix.ts', 'Formula 1'),
        ('/data/Premier   League/Liverpool.at.Chelsea.ts', 'Soccer'),
    ])
    def test_getSportFor_separators(self, path, expected):
        sportEntry = self.service.getSportFor(path)
        self.assertEqual(expected, sportEntry.name)


    @parameterized.expand([
        (None, None),
        ('NCAA.Football', 'NCAA'),
        ('Cricket', None),
        ('MLS', 'Soccer'),
        ('MLS Soccer', 'Soccer'),
        ('UEFA Champions League', 'Soccer'),
    ])
    def test_getSportFor_just_sport(self, path, expected):
        sportEntry = self.service.getSportFor(path)

        if expected is None:
            self.assertIsNone(sportEntry)
        else:
            self.assertEqual(expected, sportEntry.name)


if __name__ == '__main__':
    unittest.main()
