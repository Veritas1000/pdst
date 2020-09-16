import os
import unittest
from datetime import timedelta

from parameterized import parameterized

from pdst import parsing
from pdst.parsing import convertSpacesToRegex
from pdst.sports import TeamSpec


class TestMetadata(unittest.TestCase):

    @parameterized.expand([
        ('Some: Thing', 'Some Thing'),
        ('Some| Thing?', 'Some Thing'),
        ('Some/Thing*', 'SomeThing'),
        ('Some\\Thing%', 'SomeThing'),
        ('Some[]\' "Thing"<>', 'Some Thing'),
    ])
    def test_removeBadFilenameChars(self, original, expected):
        out = parsing.removeBadFilenameChars(original)
        self.assertEqual(expected, out)

    @parameterized.expand([
        ('1997 The Title', 'The Title'),
        ('1997 The Title 2009', 'The Title'),
        ('(1997) The Title (2009)', 'The Title'),
        ('2018 The Title 2019 (2019)', 'The Title'),
    ])
    def test_removeYears(self, original, expected):
        out = parsing.removeYears(original)
        self.assertEqual(expected, out)

    @parameterized.expand([
        ('Team One vs. Team Two', 'Team One', 'Team Two'),
        ('Team One at Team Two', 'Team One', 'Team Two'),
        ('Team_One_vs_Team_Two', 'Team_One', 'Team_Two'),
        ('Team_One_at_Team_Two', 'Team_One', 'Team_Two'),
        ('Team.One.vs.Team.Two', 'Team.One', 'Team.Two'),
        ('Team.One.at.Team.Two', 'Team.One', 'Team.Two'),
        ('Team-One-vs.-Team-Two', 'Team-One', 'Team-Two'),
        ('Team-One-at-Team-Two', 'Team-One', 'Team-Two'),
        ('Game 5 Milwaukee Bucks vs. Miami Heat', 'Game 5 Milwaukee Bucks', 'Miami Heat'),
        ('Game 5: Milwaukee Bucks vs. Miami Heat', 'Milwaukee Bucks', 'Miami Heat'),
        ('Game 5 (if necessary) Milwaukee Bucks vs. Miami Heat', 'Milwaukee Bucks', 'Miami Heat'),
    ])
    def test_teamNamesFromMatch_basic(self, input, expected1, expected2):
        matches = parsing.teamNamesFromMatch(input)
        self.assertEqual(matches[1], expected1)
        self.assertEqual(matches[2], expected2)

    @parameterized.expand([
        'Team One',
        'Team_One',
        'Game 4 Western Conference semifinal series',
    ])
    def test_teamNamesFromMatch_failure(self, inStr):
        matches = parsing.teamNamesFromMatch(inStr)
        self.assertEqual(matches, None)

    @parameterized.expand([
        ('/some/path/Team_One_000000.png', 'Team_One'),
        ('Team_One_000000.png', 'Team_One'),
        ('Team_One_000000_fefefe.png', 'Team_One'),
        ('Team_One_000_fefefe.png', 'Team_One'),
        ('Team_One_123456_fff_000i.png', 'Team_One'),
        ('Team_One_123456_fff_oops.png', 'Team_One_123456_fff_oops'),
        ('Team_One.png', 'Team_One'),
        ('Team_One_123456_fff_bg$solid.png', 'Team_One'),
        ('Team_One_123456_fff_bg$solid_222.png', 'Team_One'),
        ('Team_One_123456_fff_bg$solid_222_nope.png', 'Team_One_123456_fff_bg$solid_222_nope'),
        ('Team_One_123456_fff_mask$0f0.png', 'Team_One'),
    ])
    def test_cleanImageHints(self, input, expected):
        teamName = parsing.cleanImageHints(input)
        self.assertEqual(expected, teamName)

    @parameterized.expand([
        ('/some/path/Some_Name_000000.png', True),
        ('Some.Name.000.png', True),
        ('Some-Name.png', False),
        ('/some/path/Some-Name_fafecd_23af45.png', True),
        ('/some/path/Some-Name_fafecd_23af45_nope.png', False),
        ('Some.Name.000i.png', True),
        ('Some.Name.000I.png', True),
        ('Some_Name_ffaa88I.png', True),
        ('Some_Name_ffaa88X.png', False),
        ('Some_Name_ffaa88_bg$solid.png', True),
        ('Some_Name_ffaa88_bg$solid_Q.png', False),
        ('Some_Name_ffaa88_mask$fff.png', True),
        ('Some_Name_ffaa88_mask$fff_Q.png', False),
    ])
    def test_hasHints(self, input, expected):
        found = parsing.hasHints(input)
        self.assertEqual(expected, found)

    @parameterized.expand([
        ('/some/path/Some_Name_000000.png', '000000'),
        ('/some/path/Some_Name_000000.png', '000000', 0),
        ('/some/path/Some_Name_000000.png', '000000', 1),
        ('/some/path/Some_Name_000000.png', '000000', 2),
        ('Some_Name_000000_faf_abc123.png', 'faf', 1),
        ('Some_Name_000000_faf_abc123.png', 'abc123', 2),
        ('Some_Name_000000_faf_ABC123.png', 'ABC123', 3),
        ('Some_Name_000000_none.png', None),
        ('Some_Name_000000_none.png', None, 1),
        ('Some_Name_000000X.png', None),
        ('/some/path/Some_Name_abc123i.png', 'abc123'),
        ('/some/path/Some_Name_abc123I.png', 'abc123'),
        ('/some/path/Some_Name_abc123I_FAFi.png', 'abc123', 0),
        ('/some/path/Some_Name_abc123I_fafI_000.png', 'faf', 1),

        ('/some/path/Some_Name_000000_bg$solid.png', '000000', 0),
        ('Some_Name_000000_bg$solid_faf_abc123.png', 'faf', 1),
        ('Some_Name_bg$solid_000000_faf_abc123.png', 'abc123', 2),
        ('/some/path/Some_Name_000000_bg$stripe1.1.png', '000000', 1),
    ])
    def test_getColorFromFilename(self, path, expected, position=None):
        if position is None:
            color = parsing.getColorFromFilename(path)
        else:
            color = parsing.getColorFromFilename(path, position)

            self.assertEqual(expected, color)

    @parameterized.expand([
        ('/some/path/Some_Name_000000.png', False),
        ('/some/path/Some_Name_000000.png', False, 0),
        ('/some/path/Some_Name_000000.png', False, 1),
        ('/some/path/Some_Name_abc123i.png', True),
        ('/some/path/Some_Name_abc123I.png', True),
        ('/some/path/Some_Name_abc123I_fafi.png', True, 1),
        ('/some/path/Some_Name_abc123I_fafI_000.png', False, 2),
        ('/some/path/Some_Name_abc123I_bg$stripe.png', True),
        ('/some/path/Some_Name_abc123I_bg$stripe_fafi.png', True, 1),
        ('/some/path/Some_Name_bg$stripe_abc123I_fafI_000.png', False, 2),
    ])
    def test_isColorInverted(self, path, expected, position=None):
        if position is None:
            inverted = parsing.isColorInverted(path)
        else:
            inverted = parsing.isColorInverted(path, position)

        self.assertEqual(expected, inverted)

    @parameterized.expand([
        ('Some_Name_000000.png', '0123456', 'Some_Name_0123456.png'),
        ('Some_Name_000000_aaa.png', '0123456', 'Some_Name_0123456.png'),
        ('Some_Name.png', '0123456', 'Some_Name_0123456.png'),
        ('Some_Name_000000_aaa_oops.png', '0123456', 'Some_Name_000000_aaa_oops_0123456.png'),
        ('Some_Name_000000i.png', '0123456', 'Some_Name_0123456.png'),
        ('Some_Name_000000_aaai.png', '0123456', 'Some_Name_0123456.png'),
        ('Some_Name_000000.png', '0123456', 'Some_Name_0123456i.png', True),
        ('Some_Name_000000_aaa.png', '0123456', 'Some_Name_0123456i.png', True),
        ('Some_Name.png', '0123456', 'Some_Name_0123456i.png', True),
        ('Some_Name_000000.png', '0123456', 'Some_Name_0123456.png', False),
        ('Some_Name_000000_aaa.png', '0123456', 'Some_Name_0123456.png', False),
        ('Some_Name.png', '0123456', 'Some_Name_0123456.png', False),
    ])
    def test_setColorInFilename(self, inFile, inColor, expected, invert=None):
        if invert is None:
            out = parsing.setColorInFilename(inFile, inColor)
        else:
            out = parsing.setColorInFilename(inFile, inColor, invert)

        self.assertEqual(expected, out)

    @parameterized.expand([
        ('Premier League Soccer (2019)', 'Premier League Soccer'),
        ('Premier League Soccer', 'Premier League Soccer'),
        ('Super Rugby Aotearoa (2020)', 'Super Rugby Aotearoa'),
        ('MLS Soccer (2009)', 'MLS Soccer'),
    ])
    def test_removePlexShowYear(self, inTitle, expected):
        out = parsing.removePlexShowYear(inTitle)

        self.assertEqual(expected, out)

    @parameterized.expand([
        ('/images/Some_Name_135acf.png', None),
        ('/images/Some_Name_135acf_bg$stripe1.xyz', 'stripe1'),
        ('/images/Some_Name_135acf_bg$check_ffaaff.xyz', 'check'),
    ])
    def test_getBgPatternHint(self, inFile, expected):
        out = parsing.getBgPatternHint(inFile)

        self.assertEqual(expected, out)

    @parameterized.expand([
        ('/images/Some_Name_135acf.png', None),
        ('/images/Some_Name_135acf_bg$stripe1.xyz', None),
        ('/images/Some_Name_135acf_mask$000.xyz', '000'),
        ('/images/Some_Name_135acf_mask$abc_ffaaff.xyz', 'abc'),
    ])
    def test_getMaskHint(self, filename, expectedMaskHex):
        out = parsing.getMaskHint(filename)
        self.assertEqual(expectedMaskHex, out)

    @parameterized.expand([
        ('not teams string', False),
        ('not teams:', False),
        ('teams:', True),
        ('tEaMs:', True),
        ('TEAMS:', True),
        ('teams:1235 anything here really', True),
        ('team:', True),
        ('team:abc123LMNOP', True),
    ])
    def test_isTeamsString(self, inStr, expected):
        out = parsing.isTeamsString(inStr)

        self.assertEqual(expected, out)

    @parameterized.expand([
        ('not teams string', None),
        ('teams:Team 1--Team 2', [TeamSpec('Team 1'), TeamSpec('Team 2')]),
        ('teams:Sport 1/Team 1--Sport 1/Team 2', [TeamSpec('Team 1', 'Sport 1'), TeamSpec('Team 2', 'Sport 1')]),
        ('teams:Sport 1/Team 1--Sport 2/Team 2', [TeamSpec('Team 1', 'Sport 1'), TeamSpec('Team 2', 'Sport 2')]),
        ('teams:Team 1--Sport/Team 2', [TeamSpec('Team 1', 'Sport'), TeamSpec('Team 2', 'Sport')]),
        ('teams:--Team 2', [TeamSpec('Team 2')]),
        ('teams:Team 1--', [TeamSpec('Team 1')]),
        ('teams:Team 1', [TeamSpec('Team 1')]),
        ('team:Team 1', [TeamSpec('Team 1')]),
        ('team:Sport/Team', [TeamSpec('Team', 'Sport')]),
        ('team:Sport/Team--Team 2', [TeamSpec('Team', 'Sport'), TeamSpec('Team 2', 'Sport')]),
    ])
    def test_parseTeamsString(self, inStr, expected):
        out = parsing.parseTeamsString(inStr)

        self.assertEqual(expected, out)

    @parameterized.expand([
        ('Word', 'Word'),
        ('Two Word', 'Two[\\s\\.\\-_]+Word'),
        (' Two-Word', 'Two-Word')
    ])
    def test_convertSpacesToRegex(self, inStr, expectedMatchRegex):
        regex = convertSpacesToRegex(inStr)
        self.assertEqual(expectedMatchRegex, regex)

    @parameterized.expand([
        (None, None),
        ('', None),
        ('1d', timedelta(days=1)),
        ('2w 1d 2h', timedelta(days=1, hours=2, weeks=2)),
        ('1d 2h 3d', timedelta(days=4, hours=2)),
        ('1d2h3d', timedelta(days=4, hours=2)),
    ])
    def test_parseTimedelta(self, inStr, expectedTimedelta):
        out = parsing.parseTimedelta(inStr)
        self.assertEqual(expectedTimedelta, out)
