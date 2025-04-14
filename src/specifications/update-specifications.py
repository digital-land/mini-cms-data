#!/usr/bin/env python3

import os
from github import Github
from datetime import datetime
import yaml
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

def update_files_in_branch(repo, branch_name):
    """
    Update files in the GitHub repository branch based on the file mapping
    """
    for source, destination in FILE_MAPPING.items():
        try:
            # Read the source file from the current repository
            with open(source, 'r') as f:
                source_content = f.read()

            yaml_content = yaml.safe_load(source_content)
            content = yaml_content["data"]
            content = yaml.dump(content)

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
