import os
import shutil
import unittest
from datetime import datetime
from glob import iglob
from unittest.mock import patch

from click.testing import CliRunner

from pdst.cli import cli


def mocked_abspath(path):
    return f'/a/fake/data/path/{path}'


def mocked_rename(old, new):
    print(f"(MOCK) Rename: {old} -> {new}")
    shutil.copy(old, new)


def mocked_glob(in_glob):
    print(f"iglob: {in_glob}")
    new_glob = in_glob.replace('/a/fake/data/path', 'test-files/testMedia')
    print(new_glob)
    return iglob(new_glob)


class TestCliMove(unittest.TestCase):

    def setUp(self):
        testsDir = os.path.split(__file__)[0]
        os.chdir(testsDir)
        self.cfg = os.path.join(testsDir, 'test-files', 'config.json')

    def test_move_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['move', '--help'])

        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: cli move [OPTIONS]', result.output)

    @patch('pdst.commands.cmd_move.os.rename', side_effect=mocked_rename)
    @patch('pdst.filetools.glob.iglob', side_effect=mocked_glob)
    @patch('pdst.commands.cmd_move.os.path.isfile', return_value=True)
    @patch('pdst.commands.cmd_move.os.path.abspath', side_effect=mocked_abspath)
    def test_move_single(self, mock_abspath, mock_isfile, mocked_glob, mock_rename):
        runner = CliRunner()
        vid_file = 'Sport Alpha (2009)/Season 2020/' \
                   'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts'
        result = runner.invoke(cli, ['move', '-vv', '-c', self.cfg, vid_file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn(f'Moving /a/fake/data/path/Sport Alpha (2009)/Season 2020/'
                          'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts and associated files...', result.output)

            self.assertIn(f'Creating destination directories: test-files/out{os.path.sep}Sport Alpha{os.path.sep}Season 2020', result.output)
            self.assertIn('Destination show does not have an existing poster', result.output)
            posterPath = os.path.join('test-files/testPlexLibrary', 'Metadata', 'TV Shows', 'x', 'yz890.bundle',
                                      'Uploads', 'posters', '12345.jpg')
            self.assertIn(f"Copying 'old' library show poster: {posterPath}", result.output)

            outroot = os.path.join(os.path.split(__file__)[0], 'test-files', 'out')
            expectedSportDir = os.path.join(outroot, 'Sport Alpha')
            self.assertTrue(os.path.isdir(expectedSportDir))

            self.assertTrue(os.path.exists(os.path.join(expectedSportDir, 'poster.jpg')))

            expectedSeasonDir = os.path.join(expectedSportDir, 'Season 2020')
            self.assertTrue(os.path.isdir(expectedSeasonDir))

            zone_fixed_timestamp = datetime.fromtimestamp(1596484800)
            time_fmt = zone_fixed_timestamp.strftime('%Y-%m-%d %H %M %S')
            expected_new_filebase = 'Sport Alpha - ' + time_fmt + ' - Team Alpha vs. Team Bravo'
            for ext in ['ts', 'metadata', 'png']:
                expected_file = os.path.join(expectedSeasonDir, expected_new_filebase + '.' + ext)
                self.assertTrue(os.path.exists(expected_file), f"Expected file not present: {expected_file}")

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        finally:
            # always clean up
            if os.path.exists('test-files/out'):
                shutil.rmtree('test-files/out')
