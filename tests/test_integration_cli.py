import unittest
import json
from unittest.mock import patch
from io import StringIO
import os

# Assuming cli.py is structured as a module you can import from
from killercoda_cli import cli

class TestCLIIntegration(unittest.TestCase):
    def setUp(self):
        # Setup test environment, e.g., creating a temporary directory structure
        self.test_dir = '/tmp/test_cli_integration'
        os.makedirs(self.test_dir, exist_ok=True)
        # Create necessary files and directories for testing
        os.makedirs(os.path.join(self.test_dir, 'step1'), exist_ok=True)
        with open(os.path.join(self.test_dir, 'step1/step1.md'), 'w') as f:
            f.write("# Step 1\n")
        with open(os.path.join(self.test_dir, 'index.json'), 'w') as f:
            json.dump({"details": {"steps": [{"title": "Step 1", "text": "step1/step1.md", "background": "step1/background.sh"}]}}, f)

    @patch('builtins.input', side_effect=["title for new step", "2"])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_main_integration(self, mock_stdout, mock_input):
        # Change the current working directory to the test directory
        os.chdir(self.test_dir)


        
        # Call the main function directly
        cli.main()
        
        # Check if the CLI tool ran successfully by inspecting stdout or other side effects
        self.assertIn("File structure changes:", mock_stdout.getvalue())

    def tearDown(self):
        # Clean up the test directory after the test is complete
        os.chdir(self.test_dir)  # Return to the original directory
        os.chdir('/tmp')  # Return to the original directory
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

if __name__ == "__main__":
    unittest.main()
