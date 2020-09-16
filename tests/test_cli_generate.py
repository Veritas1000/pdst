import os
import shutil
import unittest

from PIL import Image
from click.testing import CliRunner

from pdst.cli import cli
from tests.helpers import verifyImagesEquivalent


class TestCliGenerate(unittest.TestCase):
    outDir = os.path.join(os.path.split(__file__)[0], 'test-files', 'out')

    def setUp(self):
        testsDir = os.path.split(__file__)[0]
        os.chdir(testsDir)
        self.cfg = os.path.join(testsDir, 'test-files', 'config.json')
        self.genRefDir = os.path.join(os.path.split(__file__)[0], 'test-files', 'gen-reference')

    @classmethod
    def setUpClass(cls):
        # setup temp output dir
        os.makedirs(cls.outDir)

    @classmethod
    def tearDownClass(cls):
        # cleanup temp out dir
        shutil.rmtree(cls.outDir)

    def test_generate_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['generate', '--help'])
        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Usage: cli generate [OPTIONS]', result.output)

        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_generate_video_file_force(self):
        runner = CliRunner()
        vid_file = os.path.join('test-files', 'testMedia', 'Sport Alpha (2009)', 'Season 2020',
                                'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts')
        result = runner.invoke(cli, ['generate', '-v', '-f', '-o', self.outDir, '-c', self.cfg, vid_file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Processing video file: Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts', result.output)
            self.assertIn('Saving Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.png', result.output)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_generate_video_file_no_process(self):
        runner = CliRunner()
        vid_file = os.path.join('test-files', 'testMedia', 'Sport Alpha (2009)', 'Season 2020',
                                'Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts')
        result = runner.invoke(cli, ['generate', '-v', '-c', self.cfg, vid_file])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn(f'Not processing {vid_file}', result.output)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

    def test_generate_team_spec(self):
        """
        pdst generate -c test-files/config.json team:Sport/Alpha
        """
        runner = CliRunner()
        spec = 'team:Sport/Alpha'
        result = runner.invoke(cli, ['generate', '-v', '-c', self.cfg, '-o', self.outDir, spec])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Generating image for Alpha', result.output)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Alpha.png')
        testImage = os.path.join(self.outDir, 'Alpha.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_teams_spec(self):
        """
        pdst generate -c test-files/config.json teams:Sport/Alpha--Sport/Bravo
        """
        runner = CliRunner()
        spec = 'teams:Sport/Alpha--Sport/Bravo'
        result = runner.invoke(cli, ['generate', '-v', '-c', self.cfg, '-o', self.outDir, spec])

        try:
            self.assertEqual(0, result.exit_code)
            self.assertIn('Generating image for Alpha vs. Bravo', result.output)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Alpha vs. Bravo.png')
        testImage = os.path.join(self.outDir, 'Alpha vs. Bravo.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_logos(self):
        """
        pdst generate -s 600 340 -m image test-files/logos/Bravo_031734_046564_bg\$vStripe11.png test-files/logos/Alpha_69d2e6_a1cdc5_bg\$hStripe3.png
        """
        runner = CliRunner()
        img1 = os.path.join('test-files', 'logos', 'Bravo_031734_046564_bg$vStripe11.png')
        img2 = os.path.join('test-files', 'logos', 'Alpha_69d2e6_a1cdc5_bg$hStripe3.png')
        result = runner.invoke(cli, ['generate', '-m', 'image', '-s', '600', '340', '-o', self.outDir, img1, img2])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Bravo_031734_046564_bg$vStripe11.png')
        testImage = os.path.join(self.outDir, 'Bravo_031734_046564_bg$vStripe11.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

        compareImage = os.path.join(self.genRefDir, 'Alpha_69d2e6_a1cdc5_bg$hStripe3.png')
        testImage = os.path.join(self.outDir, 'Alpha_69d2e6_a1cdc5_bg$hStripe3.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_set_size(self):
        runner = CliRunner()
        spec = 'team:Sport/Alpha'
        result = runner.invoke(cli, ['generate', '-c', self.cfg, '-o', self.outDir, '-s', '100', '100', spec])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        testImage = Image.open(os.path.join(self.outDir, 'Alpha.png'))
        self.assertEqual((100, 100), testImage.size)

    def test_generate_override_options(self):
        """
        pdst generate -s 100 100 --color aff --color faf --bg vStripe2 --invert test-files/logos/plain/Bravo.png
        """
        runner = CliRunner()
        img = os.path.join('test-files', 'logos', 'plain', 'Bravo.png')
        result = runner.invoke(cli, ['generate', '-o', self.outDir, '-s', '100', '100',
                                     '--color', 'aff', '--color', 'faf', '--bg', 'vStripe2',
                                     '--invert', img])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Bravo.png')
        testImage = os.path.join(self.outDir, 'Bravo.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_checker_bg(self):
        """
        pdst generate -c test-files/config.json --bg checker0.3 teams:Sport/Bravo--Sport/Alpha
        """
        runner = CliRunner()
        spec = 'teams:Sport/Bravo--Sport/Alpha'
        result = runner.invoke(cli, ['generate', '-c', self.cfg, '-o', self.outDir,
                                     '--bg', 'checker0.3', spec])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Bravo vs. Alpha.png')
        testImage = os.path.join(self.outDir, 'Bravo vs. Alpha.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_pinstripe_bg(self):
        """
        pdst generate -c test-files/config.json --bg pinstripe0.5 team:Sport/Alpha
        """
        runner = CliRunner()
        spec = 'team:Sport/Alpha'
        result = runner.invoke(cli, ['generate', '-c', self.cfg, '-o', self.outDir,
                                     '--bg', 'pinstripe0.5', spec])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Alpha_pinstripe.png')
        testImage = os.path.join(self.outDir, 'Alpha.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_stroke_mask(self):
        """
        pdst generate -s 100 100 --mask afa --stroke 4 85e test-files/logos/plain/Charlie.png
        """
        runner = CliRunner()
        img = os.path.join('test-files', 'logos', 'plain', 'Charlie.png')
        result = runner.invoke(cli, ['generate', '-o', self.outDir, '-s', '100', '100',
                                     '--mask', 'afa', '--stroke', '4', '85e', img])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Charlie.png')
        testImage = os.path.join(self.outDir, 'Charlie.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_stroke_mask_hints(self):
        """
        pdst generate -m image -s 100 100 test-files/logos/Charlie_0021A5_mask\$FA4616.png
        """
        runner = CliRunner()
        img = os.path.join('test-files', 'logos', 'Charlie_0021A5_mask$FA4616.png')
        result = runner.invoke(cli, ['generate', '-m', 'image', '-o', self.outDir, '-s', '100', '100', img])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Charlie_0021A5_mask$FA4616.png')
        testImage = os.path.join(self.outDir, 'Charlie_0021A5_mask$FA4616.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_text(self):
        """
        pdst generate -s 100 100 --text 'Hello World' test-files/logos/plain/Alpha.png
        """
        runner = CliRunner()
        img = os.path.join('test-files', 'logos', 'plain', 'Alpha.png')
        result = runner.invoke(cli, ['generate', '-o', self.outDir, '-s', '100', '100',
                                     '--text', 'Hello World', img])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Alpha_text.png')
        testImage = os.path.join(self.outDir, 'Alpha.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_blurzoom_bg(self):
        """
        pdst generate -s 600 340 --bg blurzoom test-files/logos/plain/Alpha.png
        """
        runner = CliRunner()
        img = os.path.join('test-files', 'logos', 'plain', 'Alpha.png')
        result = runner.invoke(cli, ['generate', '-o', self.outDir, '-s', '600', '340',
                                     '--bg', 'blurzoom', img])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Alpha_blurzoom.png')
        testImage = os.path.join(self.outDir, 'Alpha.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_generate_fillLogo_bg(self):
        """
        pdst generate -s 600 340 --bg fillLogo test-files/logos/plain/Bravo.png
        """
        runner = CliRunner()
        img = os.path.join('test-files', 'logos', 'plain', 'Bravo.png')
        result = runner.invoke(cli, ['generate', '-o', self.outDir, '-s', '600', '340',
                                     '--bg', 'fillLogo', img])

        try:
            self.assertEqual(0, result.exit_code)
        except AssertionError as e:
            print(result.output)
            print(result.exception)
            raise e

        compareImage = os.path.join(self.genRefDir, 'Bravo_fillLogo.png')
        testImage = os.path.join(self.outDir, 'Bravo.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)
