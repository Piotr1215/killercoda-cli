import unittest
import json
from unittest.mock import patch
from io import StringIO
import os

from killercoda_cli import cli

class TestCLIIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = '/tmp/test_cli_integration'
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'step1'), exist_ok=True)
        with open(os.path.join(self.test_dir, 'step1/step1.md'), 'w') as f:
            f.write("# Step 1\n")
        with open(os.path.join(self.test_dir, 'index.json'), 'w') as f:
            json.dump({"details": {"steps": [{"title": "Step 1", "text": "step1/step1.md", "background": "step1/background.sh"}]}}, f)

    @patch('sys.argv', ['killercoda-cli', '--help'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_main_help_message(self, mock_stdout):
        cli.main()
        output = mock_stdout.getvalue()
        self.assertIn("Usage: killercoda-cli [OPTIONS]", output)
        self.assertIn("A CLI helper for writing KillerCoda scenarios", output)

    @patch('builtins.input', side_effect=["title for new step", "regular", "2"])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_main_integration(self, mock_stdout, mock_input):
        os.chdir(self.test_dir)
        cli.main()
        self.assertIn("File structure changes:", mock_stdout.getvalue())

    def tearDown(self):
        os.chdir('/tmp')
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    @patch('builtins.input', side_effect=["New Step Title", "regular", "100"])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_main_invalid_step_number(self, mock_stdout, mock_input):
        os.chdir(self.test_dir)
        cli.main()
        self.assertIn("Invalid step number:", mock_stdout.getvalue())

    @patch('builtins.input', side_effect=["New Step Title", "regular", "not a number"])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_main_non_numeric_step_number(self, mock_stdout, mock_input):
        os.chdir(self.test_dir)
        cli.main()
        self.assertIn("Invalid step number:", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_main_no_step_files(self, mock_stdout):
        empty_test_dir = '/tmp/test_cli_no_steps'
        os.makedirs(empty_test_dir, exist_ok=True)
        os.chdir(empty_test_dir)
        with self.assertRaises(SystemExit) as cm:
            cli.main()
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("The 'index.json' file is missing. Please ensure it is present in the current directory.", mock_stdout.getvalue())
        os.rmdir(empty_test_dir)

if __name__ == "__main__":
    unittest.main()
