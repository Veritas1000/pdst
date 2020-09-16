import os
import shutil
import unittest

from click.testing import CliRunner

from pdst.cli import cli


class TestCliGenerate(unittest.TestCase):
    cleanRoot = os.path.join(os.path.dirname(__file__), 'test-files', 'cleanTest')

    def setUp(self):
        testsDir = os.path.dirname(__file__)
        os.chdir(testsDir)

        testMediaDir = os.path.join(os.path.split(__file__)[0], 'test-files', 'testMedia')
        shutil.copytree(testMediaDir, self.cleanRoot)

    def tearDown(self):
        # cleanup temp out dir
        shutil.rmtree(self.cleanRoot)

    def test_clean_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['clean', '--help'])
        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Usage: cli clean [OPTIONS] PATH...', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_clean_removes_orphaned_files(self):
        targetDir = os.path.join(self.cleanRoot, 'Sport Alpha (2009)', 'Season 2020')
        originalBasename = 'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo'

        originalMetadata = os.path.join(targetDir, f'{originalBasename}.metadata')
        originalImage = os.path.join(targetDir, f'{originalBasename}.png')
        originalVideo = os.path.join(targetDir, f'{originalBasename}.ts')

        orphanMetadata = os.path.join(targetDir, 'orphan.metadata')
        orphanImage = os.path.join(targetDir, 'orphan.png')

        shutil.copy(originalMetadata, orphanMetadata)
        shutil.copy(originalImage, orphanImage)

        runner = CliRunner()
        result = runner.invoke(cli, ['clean', '-R', self.cleanRoot])
        try:
            self.assertEqual(0, result.exit_code)

            self.assertFalse(os.path.exists(orphanMetadata))
            self.assertFalse(os.path.exists(orphanImage))

            self.assertTrue(os.path.exists(originalMetadata))
            self.assertTrue(os.path.exists(originalImage))
            self.assertTrue(os.path.exists(originalVideo))

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_clean_skips_posters(self):
        targetDir = os.path.join(self.cleanRoot, 'Sport Alpha (2009)', 'Season 2020')
        originalBasename = 'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo'

        originalImage = os.path.join(targetDir, f'{originalBasename}.png')

        posterImage = os.path.normpath(os.path.join(targetDir, '..', 'poster.png'))

        shutil.copy(originalImage, posterImage)

        runner = CliRunner()
        result = runner.invoke(cli, ['clean', '-R', self.cleanRoot])
        try:
            self.assertEqual(0, result.exit_code)

            self.assertTrue(os.path.exists(posterImage))

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_clean_older(self):
        targetDir = os.path.join(self.cleanRoot, 'Sport Alpha (2009)', 'Season 2020')
        oldBasename = 'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo'

        oldMetadata = os.path.join(targetDir, f'{oldBasename}.metadata')
        oldImage = os.path.join(targetDir, f'{oldBasename}.png')
        oldVideo = os.path.join(targetDir, f'{oldBasename}.ts')

        newBasename = 'Sport Alpha (2009) - 2020-12-31 12 00 00 - Team Alpha vs. Team Bravo'
        newMetadata = os.path.join(targetDir, f'{newBasename}.metadata')
        newImage = os.path.join(targetDir, f'{newBasename}.png')
        newVideo = os.path.join(targetDir, f'{newBasename}.ts')

        shutil.copy(oldMetadata, newMetadata)
        shutil.copy(oldImage, newImage)
        shutil.copy(oldVideo, newVideo)

        runner = CliRunner()
        result = runner.invoke(cli, ['clean', '-vv', '--older', '1d', targetDir])
        try:
            self.assertEqual(0, result.exit_code)

            self.assertTrue(os.path.exists(newMetadata))
            self.assertTrue(os.path.exists(newImage))
            self.assertTrue(os.path.exists(newVideo))

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e
