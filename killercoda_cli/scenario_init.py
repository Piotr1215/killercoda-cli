import json
import os
import inquirer

backends = {
    "kubernetes-kubeadm-1node": "Kubernetes kubeadm 1 node",
    "kubernetes-kubeadm-2nodes": "Kubernetes kubeadm 2 nodes",
    "kubernetes-kubeadm-1node-4GB": "Kubeadm cluster with one control plane, taint removed, ready to schedule workload, 4GB environment",
    "ubuntu-4GB": "Ubuntu 20.04 with Docker and Podman, 4GB environment",
    "ubuntu": "Ubuntu 20.04"
}

time_choices = [f"{i} minutes" for i in range(15, 50, 5)]
difficulty_choices = ["beginner", "intermediate", "advanced"]

def get_value(prompt, value_type, choices=None):
    if choices:
        question = [inquirer.List('choice', message=prompt, choices=choices)]
        answer = inquirer.prompt(question)
        return answer['choice']
    else:
        if value_type == "boolean":
            question = [inquirer.Confirm('confirm', message=prompt, default=True)]
            answer = inquirer.prompt(question)
            return answer['confirm']
        else:
            question = [inquirer.Text('value', message=prompt)]
            answer = inquirer.prompt(question)
            return answer['value']

def populate_schema(schema, parent_key=""):
    result = {}
    for key, value_type in schema.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value_type, dict):
            result[key] = populate_schema(value_type, full_key)
        elif isinstance(value_type, list):
            if full_key == "details.steps" or full_key == "details.assets.host01":
                result[key] = []  # Initialize as empty list
            else:
                result[key] = []
                while True:
                    add_item = get_value(f"Do you want to add an item to the list '{full_key}'?", "boolean")
                    if add_item:
                        result[key].append(populate_schema(value_type[0], full_key))
                    else:
                        break
        else:
            if full_key == "time":
                result[key] = get_value(f"Select value for {full_key}", value_type, time_choices)
            elif full_key == "difficulty":
                result[key] = get_value(f"Select value for {full_key}", value_type, difficulty_choices)
            elif full_key == "backend.imageid":
                result[key] = get_value(f"Select value for {full_key}", value_type, backends)
            else:
                result[key] = get_value(f"Enter value for {full_key}", value_type)
    return result

def init_project():
    """initialize a new project by creating index.json file"""
    if os.path.exists("index.json"):
        print("The 'index.json' file already exists. Please edit the existing file.")
        return
    
    schema = {
        "title": "string",
        "description": "string",
        "difficulty": "string",
        "time": "string",
        "details": {
            "steps": [
                {}
            ],
            "assets": {
                "host01": [
                    {}
                ]
            }
        },
        "backend": {
            "imageid": "string"
        }
    }

    populated_data = populate_schema(schema)
    
    # Set static values for intro and finish
    populated_data["details"]["intro"] = {"text": "intro.md"}
    populated_data["details"]["finish"] = {"text": "finish.md"}

    if get_value("Do you want to enable Theia?", "boolean"):
        populated_data["interface"] = {"layout": "ide"}

    with open("index.json", "w") as index_file:
        json.dump(populated_data, index_file, ensure_ascii=False, indent=4)
    
    # Create intro.md and finish.md if they don't exist
    if not os.path.exists("intro.md"):
        with open("intro.md", "w") as intro_file:
            intro_file.write("# Introduction\n")

    if not os.path.exists("finish.md"):
        with open("finish.md", "w") as finish_file:
            finish_file.write("# Finish\n")

    print("Project initialized successfully. Please edit the 'index.json' file to add steps.")
