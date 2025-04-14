#!/usr/bin/env python3

import os
from github import Github
from datetime import datetime

# GitHub repository details
REPO_NAME = "digital-land/specification"
BRANCH_NAME = f"update-specifications-{datetime.now().strftime('%Y%m%d')}"
FILE_MAPPING = [
    { source: "data/collections/specifications/article-4-direction.yml", destination: "content/specification/article-4-direction.md"},
    { source: "data/collections/specifications/brownfield-land.yml", destination: "content/specification/brownfield-land.md"},
    { source: "data/collections/specifications/conservation-area.yml", destination: "content/specification/conservation-area.md"},
    { source: "data/collections/specifications/listed-building.yml", destination: "content/specification/listed-building.md"},
    { source: "data/collections/specifications/tree-preservation-order.yml", destination: "content/specification/tree-preservation-order.md"}
]

def update_files_in_branch(repo, branch_name):
    """
    Update files in the GitHub repository branch based on the file mapping
    """
    for file in FILE_MAPPING:
        try:
            # Read the source file from the current repository
            with open(file["source"], 'r') as f:
                content = f.read()

            # Get the file from GitHub repository if it exists
            try:
                file = repo.get_contents(file["destination"], ref=branch_name)
                # Update existing file
                repo.update_file(
                    path=file["destination"],
                    message=f"Update {file['destination']}",
                    content=content,
                    sha=file.sha,
                    branch=branch_name
                )
            except:
                # Create new file if it doesn't exist
                repo.create_file(
                    path=file["destination"],
                    message=f"Create {file['destination']}",
                    content=content,
                    branch=branch_name
                )

            print(f"Successfully updated {file['destination']}")

        except Exception as e:
            print(f"Error updating {file['destination']}: {str(e)}")
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
    title = f"[Mini CMS] Update specifications {datetime.now().strftime('%Y%m%d')}"
    body = "This PR updates the specifications based on the latest changes from the Mini CMS."

    create_pull_request(token, title, body)
