import unittest

from click.testing import CliRunner
from pdst.cli import cli


class TestCli(unittest.TestCase):
    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        self.assertEqual(0, result.exit_code)
        self.assertIn('meta-export', result.output)
        self.assertIn('generate', result.output)
        self.assertIn('move', result.output)
        self.assertIn('clean', result.output)
        self.assertIn('analyze', result.output)

    def test_main_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        self.assertEqual(0, result.exit_code)
        self.assertIn(', version', result.output)
