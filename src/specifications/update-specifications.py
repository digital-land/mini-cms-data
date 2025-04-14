#!/usr/bin/env python3

import os
from github import Github
from datetime import datetime
import yaml
from collections import OrderedDict

# Load schema
with open('src/specifications/schema.yml', 'r') as f:
    SCHEMA = yaml.safe_load(f)

def ordered_dict_representer(self, value):
    return self.represent_mapping('tag:yaml.org,2002:map', value.items())
yaml.add_representer(OrderedDict, ordered_dict_representer)

def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
yaml.add_representer(str, str_presenter)

# GitHub repository details
REPO_NAME = "dilwoarh/digital-land-specification"
BRANCH_NAME = f"update-specifications-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
FILE_MAPPING = {
    "data/collections/specifications/article-4-direction.yml": "content/specification/article-4-direction.md",
    "data/collections/specifications/brownfield-land.yml": "content/specification/brownfield-land.md",
    "data/collections/specifications/conservation-area.yml": "content/specification/conservation-area.md",
    "data/collections/specifications/listed-building.yml": "content/specification/listed-building.md",
    "data/collections/specifications/tree-preservation-order.yml": "content/specification/tree-preservation-order.md"
}

def get_spec_type(filename):
    """Extract specification type from filename"""
    return os.path.basename(filename).replace('.yml', '')

def order_data(data, spec_type):
    """Order data according to schema"""
    if spec_type not in SCHEMA['specifications']:
        return data

    schema = SCHEMA['specifications'][spec_type]
    ordered_data = OrderedDict()

    # Order top-level fields
    for field in schema['order']:
        if field in data:
            ordered_data[field] = data[field]

    return ordered_data

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
            yaml_content = yaml.safe_load(source_content)
            content = yaml_content["data"]

            # Get specification type and order data
            spec_type = get_spec_type(source)
            content = order_data(content, spec_type)

            # Dump YAML with ordered data and frontmatter markers
            content = yaml.dump(content,
                                sort_keys=False,
                                allow_unicode=True,
                                default_flow_style=False,
                                indent=2,
                                width=1000
                                )
            content = f"---\n{content}---\n"

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
    title = f"[Mini CMS] Update specifications {datetime.now().strftime('%Y%m%d-%H%M%S')}"
    body = "This PR updates the specifications based on the latest changes from the Mini CMS."

    create_pull_request(token, title, body)
