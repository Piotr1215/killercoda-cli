import unittest
from unittest import mock
from unittest.mock import patch
from killercoda_cli import scenario_init

class TestScenarioInit(unittest.TestCase):

    @patch("inquirer.prompt")
    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock.mock_open)
    @patch("json.dump")
    def test_init_project(self, mock_json_dump, mock_open, mock_exists, mock_prompt):
        mock_prompt.side_effect = [
            {'value': 'Project Title'},
            {'value': 'Project Description'},
            {'choice': 'beginner'},
            {'choice': '15 minutes'},
            {'choice': 'kubernetes-kubeadm-1node'},
            {'confirm': True}
        ]
        
        scenario_init.init_project()

        expected_data = {
            "title": "Project Title",
            "description": "Project Description",
            "difficulty": "beginner",
            "time": "15 minutes",
            "details": {
                "intro": {"text": "intro.md"},
                "finish": {"text": "finish.md"},
                "steps": [],
                "assets": {"host01": []}
            },
            "backend": {"imageid": "kubernetes-kubeadm-1node"},
            "interface": {"layout": "ide"}
        }

        # Check that the index.json file was created with the expected data
        calls = [
            mock.call("index.json", "w"),
            mock.call("intro.md", "w"),
            mock.call("finish.md", "w")
        ]
        mock_open.assert_has_calls(calls, any_order=True)
        mock_json_dump.assert_called_once_with(expected_data, mock.ANY, ensure_ascii=False, indent=4)

    @patch("os.path.exists", return_value=True)
    @patch("builtins.print")
    def test_init_project_existing_index(self, mock_print, mock_exists):
        scenario_init.init_project()
        mock_print.assert_called_once_with("The 'index.json' file already exists. Please edit the existing file.")

    @patch("os.path.exists", side_effect=lambda path: path == "intro.md")
    @patch("builtins.open", new_callable=mock.mock_open)
    @patch("inquirer.prompt")
    def test_init_project_create_finish_md(self, mock_prompt, mock_open, mock_exists):
        mock_prompt.side_effect = [
            {'value': 'Project Title'},
            {'value': 'Project Description'},
            {'choice': 'beginner'},
            {'choice': '15 minutes'},
            {'choice': 'kubernetes-kubeadm-1node'},
            {'confirm': True}
        ]
        
        scenario_init.init_project()
        mock_open.assert_any_call("finish.md", "w")
        mock_open().write.assert_any_call("# Finish\n")

    @patch("os.path.exists", side_effect=lambda path: path == "finish.md")
    @patch("builtins.open", new_callable=mock.mock_open)
    @patch("inquirer.prompt")
    def test_init_project_create_intro_md(self, mock_prompt, mock_open, mock_exists):
        mock_prompt.side_effect = [
            {'value': 'Project Title'},
            {'value': 'Project Description'},
            {'choice': 'beginner'},
            {'choice': '15 minutes'},
            {'choice': 'kubernetes-kubeadm-1node'},
            {'confirm': True}
        ]
        
        scenario_init.init_project()
        mock_open.assert_any_call("intro.md", "w")
        mock_open().write.assert_any_call("# Introduction\n")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock.mock_open)
    @patch("json.dump")
    @patch("inquirer.prompt")
    def test_init_project_files_created(self, mock_prompt, mock_json_dump, mock_open, mock_exists):
        mock_prompt.side_effect = [
            {'value': 'Project Title'},
            {'value': 'Project Description'},
            {'choice': 'beginner'},
            {'choice': '15 minutes'},
            {'choice': 'kubernetes-kubeadm-1node'},
            {'confirm': True}
        ]
        
        scenario_init.init_project()
        mock_open.assert_any_call("intro.md", "w")
        mock_open().write.assert_any_call("# Introduction\n")
        mock_open.assert_any_call("finish.md", "w")
        mock_open().write.assert_any_call("# Finish\n")

if __name__ == "__main__":
    unittest.main()
