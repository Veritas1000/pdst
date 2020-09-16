import os
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from pdst.cli import cli


def mocked_abspath(path):
    return f'/a/fake/data/path/{path}'


def mocked_open(filename, mode):
    new_filename = get_test_filename(filename)
    return open(new_filename, mode)


def get_test_filename(original):
    testsDir = os.path.dirname(__file__)
    (dirname, basename) = os.path.split(original)
    new_filename = os.path.join(testsDir, 'test-files', basename)
    return new_filename


class TestCliMetadataExport(unittest.TestCase):

    def setUp(self):
        testsDir = os.path.split(__file__)[0]
        os.chdir(testsDir)
        self.cfg = os.path.join(testsDir, 'test-files', 'config.json')

    def test_meta_export_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['meta-export', '--help'])

        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: cli meta-export [OPTIONS]', result.output)

    @patch('pdst.commands.cmd_meta-export.os.path.abspath', side_effect=mocked_abspath)
    def test_meta_export_dont_process(self, mock_abspath):
        """When passed a single path that is not a file, it is not processed further"""
        runner = CliRunner()
        result = runner.invoke(cli, ['meta-export', '-vv', '-c', self.cfg, 'non-existent/file/or/dir'])

        self.assertEqual(0, result.exit_code)
        self.assertIn('not processing /a/fake/data/path/non-existent/file/or/dir', result.output)

    @patch('pdst.commands.cmd_meta-export.os.path.exists', return_value=True)
    @patch('pdst.commands.cmd_meta-export.os.path.isfile', return_value=True)
    @patch('pdst.commands.cmd_meta-export.os.path.abspath', side_effect=mocked_abspath)
    def test_meta_export_single_file_has_metadata(self, mock_abspath, mock_isfile, mock_exists):
        """When passed a file that has an existing metadata file, default to not processing"""
        runner = CliRunner()
        result = runner.invoke(cli, ['meta-export', '-vv', '-c', self.cfg, 'file/with/metadata.mkv'])

        self.assertEqual(0, result.exit_code)
        self.assertIn('Has metadata file?: /a/fake/data/path/file/with/metadata.mkv : True', result.output)
        self.assertIn('not processing /a/fake/data/path/file/with/metadata.mkv', result.output)

    @patch('pdst.commands.cmd_meta-export.os.path.exists', return_value=True)
    @patch('pdst.commands.cmd_meta-export.os.path.isfile', return_value=True)
    @patch('pdst.commands.cmd_meta-export.os.path.abspath', side_effect=mocked_abspath)
    def test_meta_export_single_file_forced_no_db(self, mock_abspath, mock_isfile, mock_exists):
        """
        When passed a file that has an existing metadata file with the --force flag, process anyways
        BUT this one doesn't have metadata in the DB
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['meta-export', '-vv', '-c', self.cfg, '--force', 'file/with/metadata.mkv'])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Has metadata file?: /a/fake/data/path/file/with/metadata.mkv : True', result.output)
            self.assertIn('Processing /a/fake/data/path/file/with/metadata.mkv', result.output)
            self.assertIn('NO metadata found in db for /a/fake/data/path/file/with/metadata.mkv!', result.output)

        except AssertionError as e:
            print(e)
            print(result.output)
            print(result.exception)
            raise e

    @patch('pdst.db.metadata.open', side_effect=mocked_open)
    @patch('pdst.commands.cmd_meta-export.os.path.exists', return_value=False)
    @patch('pdst.commands.cmd_meta-export.os.path.isfile', return_value=True)
    @patch('pdst.commands.cmd_meta-export.os.path.abspath', side_effect=mocked_abspath)
    def test_meta_export_single_file(self, mock_abspath, mock_isfile, mock_exists, mocked_open):
        """Verify metadata file is written when processed and there is data in the plex db"""
        runner = CliRunner()
        vid_file = 'Sport Alpha (2009)/Season 2020/' \
                   'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts'
        expected_outfile = os.path.splitext(get_test_filename(vid_file))[0] + '.metadata'
        result = runner.invoke(cli, ['meta-export', '-vv', '-c', self.cfg, vid_file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.isfile(expected_outfile))

            with open(expected_outfile) as f:
                lines = [line.rstrip('\n') for line in f]

                self.assertEqual('[metadata]', lines[0])
                self.assertIn('title=Team Alpha vs. Team Bravo', lines)
                self.assertIn('summary=A match between Team Alpha and Team Bravo', lines)
                self.assertIn('release=2020-08-03', lines)

        except Exception as e:
            print(e)
            print(result.output)
            print(result.exception)
            raise e

        finally:
            # always clean up
            os.remove(expected_outfile)