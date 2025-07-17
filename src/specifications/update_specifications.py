#!/usr/bin/env python3

import os
from github import Github
from datetime import datetime
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PlainScalarString
from ruamel.yaml.nodes import ScalarNode
from io import StringIO

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.width = 4096  # Allow for long lines

# Add custom representer for multi-line strings
def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.representer.add_representer(str, str_presenter)

def quoted_key_representer(dumper, data):
    return ScalarNode(tag='tag:yaml.org,2002:str', value=data, style=None)

yaml.representer.add_representer(PlainScalarString, quoted_key_representer)

# GitHub repository details
REPO_NAME = "digital-land/specification"
BRANCH_NAME = f"mini-cms/update-specifications-{datetime.now().strftime('%Y-%m-%d--%H-%M-%S')}"
FILE_MAPPING = {
    "data/collections/specifications/article-4-direction.yml": "content/specification/article-4-direction.md",
    "data/collections/specifications/brownfield-land.yml": "content/specification/brownfield-land.md",
    "data/collections/specifications/conservation-area.yml": "content/specification/conservation-area.md",
    "data/collections/specifications/listed-building.yml": "content/specification/listed-building.md",
    "data/collections/specifications/tree-preservation-order.yml": "content/specification/tree-preservation-order.md"
}

def get_data_order():
    """Get the order of fields from the config file"""
    with open('config.yml', 'r') as f:
        config = yaml.load(f)

    # Find the specifications collection
    for collection in config['collections']:
        if collection['id'] == 'specifications':
            # Extract field IDs from the fields section
            return [field['id'] for field in collection['fields'] if isinstance(field, dict) and 'id' in field]

    return []

def order_data(data):
    """Order data according to schema"""
    ordered_data = {}
    data_order = get_data_order()

    # Order top-level fields
    for field in data_order:
        if field in data:
            if field == 'datasets' and isinstance(data[field], list):
                # Handle datasets array - order each dataset according to its schema
                ordered_datasets = []
                for dataset in data[field]:
                    ordered_dataset = order_dataset(dataset)
                    ordered_datasets.append(ordered_dataset)
                ordered_data[PlainScalarString(field)] = ordered_datasets
            else:
                ordered_data[PlainScalarString(field)] = data[field]

    return ordered_data

def order_dataset(dataset):
    """Order dataset fields according to schema"""
    ordered_dataset = {}

    # Get dataset field order from config
    dataset_field_order = get_dataset_field_order()

    for field in dataset_field_order:
        if field in dataset:
            if field == 'fields' and isinstance(dataset[field], list):
                # Handle fields array - order each field according to its schema
                ordered_fields = []
                for field_item in dataset[field]:
                    ordered_field = order_field(field_item)
                    ordered_fields.append(ordered_field)
                ordered_dataset[PlainScalarString(field)] = ordered_fields
            else:
                ordered_dataset[PlainScalarString(field)] = dataset[field]

    return ordered_dataset

def order_field(field_item):
    """Order field properties according to schema"""
    ordered_field = {}

    # Get field property order from config
    field_property_order = get_field_property_order()

    for prop in field_property_order:
        if prop in field_item:
            ordered_field[PlainScalarString(prop)] = field_item[prop]

    return ordered_field

def get_dataset_field_order():
    """Get the order of dataset fields from the config file"""
    with open('config.yml', 'r') as f:
        config = yaml.load(f)

    # Find the specifications collection
    for collection in config['collections']:
        if collection['id'] == 'specifications':
            # Find the datasets field
            for field in collection['fields']:
                if isinstance(field, dict) and field.get('id') == 'datasets':
                    # Extract field IDs from the datasets fields section
                    return [f['id'] for f in field['fields'] if isinstance(f, dict) and 'id' in f]

    return []

def get_field_property_order():
    """Get the order of field properties from the config file"""
    with open('config.yml', 'r') as f:
        config = yaml.load(f)

    # Find the specifications collection
    for collection in config['collections']:
        if collection['id'] == 'specifications':
            # Find the datasets field
            for field in collection['fields']:
                if isinstance(field, dict) and field.get('id') == 'datasets':
                    # Find the fields field within datasets
                    for dataset_field in field['fields']:
                        if isinstance(dataset_field, dict) and dataset_field.get('id') == 'fields':
                            # Extract field IDs from the fields section
                            return [f['id'] for f in dataset_field['fields'] if isinstance(f, dict) and 'id' in f]

    return []

def update_files_in_branch(repo, branch_name):
    """
    Update files in the GitHub repository branch based on the file mapping
    """
    for source, destination in FILE_MAPPING.items():
        try:
            # Read the source file from the current repository
            with open(source, 'r') as f:
                source_content = f.read()

            # Load YAML content
            yaml_content = yaml.load(source_content)
            content = yaml_content["data"]

            # Get specification type and order data
            content = order_data(content)

            # Dump YAML with ordered data and frontmatter markers
            buffer = StringIO()
            yaml.dump(content, buffer)
            content = f"---\n{buffer.getvalue().strip()}\n"

            # Get the file from GitHub repository if it exists
            try:
                file = repo.get_contents(destination, ref=branch_name)
                # Update existing file
                repo.update_file(
                    path=destination,
                    message=f"Update {destination}",
                    content=content,
                    sha=file.sha,
                    branch=branch_name
                )
            except:
                # Create new file if it doesn't exist
                repo.create_file(
                    path=destination,
                    message=f"Create {destination}",
                    content=content,
                    branch=branch_name
                )

            print(f"Successfully updated {destination}")

        except Exception as e:
            print(f"Error updating {destination}: {str(e)}")
            raise

def create_pull_request(token, title, body):
    """
    Create a pull request on GitHub
    """
    try:
        # Initialize GitHub client
        g = Github(token)
        repo = g.get_repo(REPO_NAME)

        # Create a new branch
        main_branch = repo.get_branch("main")
        repo.create_git_ref(
            ref=f"refs/heads/{BRANCH_NAME}",
            sha=main_branch.commit.sha
        )

        # Update files in the branch
        update_files_in_branch(repo, BRANCH_NAME)

        # Create pull request
        pr = repo.create_pull(
            title=title,
            body=body,
            head=BRANCH_NAME,
            base="main"
        )

        print(f"Pull request created successfully: {pr.html_url}")
        return pr

    except Exception as e:
        print(f"Error creating pull request: {str(e)}")
        raise

if __name__ == "__main__":
    # Get GitHub token from environment variable
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")

    # Create pull request
    title = f"[Mini CMS] Update specifications {datetime.now().strftime('%Y-%m-%d--%H-%M-%S')}"
    body = "This PR updates the specifications based on the latest changes from the Mini CMS."

    create_pull_request(token, title, body)
