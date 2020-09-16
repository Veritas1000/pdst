import os
import unittest

from click.testing import CliRunner

from pdst.cli import cli


class TestCliAnalyze(unittest.TestCase):

    def setUp(self):
        testsDir = os.path.split(__file__)[0]
        os.chdir(testsDir)
        self.cfg = os.path.join(testsDir, 'test-files', 'config.json')

    def test_analyze_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', '--help'])

        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: cli analyze [OPTIONS]', result.output)

    def test_analyze_video(self):
        runner = CliRunner()
        vid_file = 'test-files/testMedia/Sport Alpha (2009)/Season 2020/' \
                   'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts'
        result = runner.invoke(cli, ['analyze', '-f', '-c', self.cfg, vid_file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('---- Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts ----', result.output)
            self.assertIn(f'Sport Alpha/Team Alpha: test-files/logos/plain{os.path.sep}Alpha.png', result.output)
            self.assertIn(f'Sport Alpha/Team Bravo: test-files/logos/plain{os.path.sep}Bravo.png', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_analyze_image(self):
        runner = CliRunner()
        file = 'test-files/logos/plain/Alpha.png'
        result = runner.invoke(cli, ['analyze', '-m', 'image', '-c', self.cfg, file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('The most common color in test-files/logos/plain/Alpha.png is #', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_analyze_dir(self):
        runner = CliRunner()
        imgDir = 'test-files/logos/plain'
        result = runner.invoke(cli, ['analyze', '-m', 'image', '-c', self.cfg, imgDir])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn(f'The most common color in test-files/logos/plain{os.path.sep}Alpha.png is #', result.output)
            self.assertIn(f'The most common color in test-files/logos/plain{os.path.sep}Bravo.png is #', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_analyze_all(self):
        runner = CliRunner()
        file = 'test-files/logos/plain/Alpha.png'
        result = runner.invoke(cli, ['analyze', '-m', 'image', '-a', '-c', self.cfg, file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Colors in test-files/logos/plain/Alpha.png from most to least common:', result.output)
            self.assertIn('[0] #', result.output)
            self.assertIn('[1] #', result.output)
            self.assertIn('[2] #', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_analyze_rename(self):
        runner = CliRunner()
        file = 'test-files/logos/plain/Alpha.png'
        result = runner.invoke(cli, ['analyze', '-m', 'image', '-c', self.cfg, '-r', file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('The most common color in test-files/logos/plain/Alpha.png is #6', result.output)
            self.assertIn(f'test-files/logos/plain/Alpha.png -> test-files/logos/plain{os.path.sep}Alpha_6', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        finally:
            # rename file back to Alpha.png
            newFile = result.output.split('\n')[-2].split(' -> ')[-1]
            os.rename(newFile, file)
