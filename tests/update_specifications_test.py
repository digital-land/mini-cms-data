import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from ruamel.yaml import YAML
from io import StringIO
from github.GithubException import BadCredentialsException
from src.specifications.update_specifications import (
    order_data,
    update_files_in_branch,
    create_pull_request,
    REPO_NAME,
    get_data_order
)

# Test data
TEST_YAML_CONTENT = {
    'data': {
        'specification': 'test-spec',
        'name': 'Test name',
        'plural': 'Test names',
        'specification-status': 'candidate-standard',
        'start-date': '2024-01-01',
        'end-date': '',
        'entry-date': '2024-01-01',
        'github-discussion': '123',
        'version': '1.0.0',
        'datasets': [
            {
                'dataset': 'test-dataset',
                'name': 'Test dataset',
                'fields': [
                    {'field': 'field1', 'description': 'Field 1'},
                    {'field': 'field2', 'description': 'Field 2'}
                ]
            }
        ]
    }
}

@pytest.fixture
def mock_repo():
    with patch('github.Github.get_repo') as mock_get_repo:
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        yield mock_repo

@pytest.fixture
def mock_file():
    mock_file = MagicMock()
    mock_file.sha = 'test_sha'
    return mock_file

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data(mock_yaml_load, mock_open):
    """Test ordering data according to schema"""
    # Mock the config file content
    mock_yaml_load.return_value = {
        'collections': [
            {
                'id': 'specifications',
                'fields': [
                    {'id': 'specification'},
                    {'id': 'name'},
                    {'id': 'plural'},
                    {'id': 'specification-status'},
                    {'id': 'start-date'},
                    {'id': 'end-date'},
                    {'id': 'entry-date'},
                    {'id': 'github-discussion'},
                    {'id': 'version'},
                    {'id': 'datasets'}
                ]
            }
        ]
    }

    # Test with all fields
    data = {
        'specification': 'test-spec',
        'name': 'Test name',
        'plural': 'Test names',
        'specification-status': 'candidate-standard',
        'start-date': '2024-01-01',
        'end-date': '',
        'entry-date': '2024-01-01',
        'github-discussion': '123',
        'version': '1.0.0',
        'datasets': [],
        'extra_field': 'should be last'
    }
    ordered = order_data(data)
    # Check that all fields are in the correct order and extra fields are excluded
    expected_order = ['specification', 'name', 'plural', 'specification-status', 'start-date',
                     'end-date', 'entry-date', 'github-discussion', 'version', 'datasets']
    assert list(ordered.keys()) == expected_order
    assert 'extra_field' not in ordered

    # Test with missing fields
    data = {
        'name': 'Test name',
        'version': '1.0.0',
    }
    ordered = order_data(data)
    assert list(ordered.keys()) == ['name', 'version']

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
@patch('ruamel.yaml.YAML.dump')
def test_update_files_in_branch(mock_yaml_dump, mock_yaml_load, mock_open, mock_repo, mock_file):
    """Test updating files in GitHub branch"""
    # Setup mocks for config file and source file
    mock_file_handle = MagicMock()
    mock_file_handle.__enter__.return_value = mock_file_handle
    mock_open.return_value = mock_file_handle
    mock_file_handle.read.return_value = "test content"

    # Mock YAML load for both config file and source file
    config_yaml = {
        'collections': [
            {
                'id': 'specifications',
                'fields': [
                    {'id': 'specification'},
                    {'id': 'name'},
                    {'id': 'plural'},
                    {'id': 'specification-status'},
                    {'id': 'start-date'},
                    {'id': 'end-date'},
                    {'id': 'entry-date'},
                    {'id': 'github-discussion'},
                    {'id': 'version'},
                    {'id': 'datasets'}
                ]
            }
        ]
    }

    source_yaml = {
        'data': {
            'specification': 'test-spec',
            'name': 'Test name',
            'plural': 'Test names',
            'specification-status': 'candidate-standard',
            'start-date': '2024-01-01',
            'end-date': '',
            'entry-date': '2024-01-01',
            'github-discussion': '123',
            'version': '1.0.0',
            'datasets': [
                {
                    'dataset': 'test-dataset',
                    'name': 'Test dataset',
                    'fields': [
                        {'field': 'field1', 'description': 'Field 1'},
                        {'field': 'field2', 'description': 'Field 2'}
                    ]
                }
            ]
        }
    }

    # Set up mock YAML load to return different values for config and source files
    def mock_yaml_load_side_effect(content):
        if content == "test content":
            return source_yaml
        return config_yaml

    mock_yaml_load.side_effect = mock_yaml_load_side_effect

    mock_repo.get_contents.return_value = mock_file
    mock_repo.update_file.return_value = {'commit': {'sha': 'test_sha'}}

    # Mock StringIO for YAML dump
    buffer = StringIO()
    buffer.write("---\n")
    buffer.write("specification: test-spec\n")
    buffer.write("name: Test name\n")
    buffer.write("plural: Test names\n")
    buffer.write("specification-status: candidate-standard\n")
    buffer.write("start-date: '2024-01-01'\n")
    buffer.write("end-date: ''\n")
    buffer.write("entry-date: '2024-01-01'\n")
    buffer.write("github-discussion: '123'\n")
    buffer.write("version: 1.0.0\n")
    buffer.write("datasets:\n")
    buffer.write("  - dataset: test-dataset\n")
    buffer.write("    name: Test dataset\n")
    buffer.write("    fields:\n")
    buffer.write("      - field: field1\n")
    buffer.write("        description: Field 1\n")
    buffer.write("      - field: field2\n")
    buffer.write("        description: Field 2\n")
    mock_yaml_dump.return_value = buffer

    # Test file update
    update_files_in_branch(mock_repo, 'test-branch')

    # Verify GitHub API calls
    mock_repo.get_contents.assert_called()
    mock_repo.update_file.assert_called()

@patch('src.specifications.update_specifications.Github')
def test_create_pull_request(mock_github_class):
    """Test creating a pull request"""
    # Setup mock GitHub instance
    mock_github = MagicMock()
    mock_github_class.return_value = mock_github

    # Setup mock repository
    mock_repo = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    # Mock the branch and commit
    mock_branch = MagicMock()
    mock_commit = MagicMock()
    mock_commit.sha = 'test_sha'
    mock_branch.commit = mock_commit
    mock_repo.get_branch.return_value = mock_branch

    # Mock the reference creation
    mock_ref = MagicMock()
    mock_repo.create_git_ref.return_value = mock_ref

    # Mock the pull request creation
    mock_pull = MagicMock()
    mock_pull.html_url = 'https://github.com/test/pr'
    mock_repo.create_pull.return_value = mock_pull

    # Test PR creation
    pr = create_pull_request('test_token', 'Test PR', 'Test body')

    # Verify GitHub API calls
    mock_github.get_repo.assert_called_once_with(REPO_NAME)
    mock_repo.get_branch.assert_called_once_with('main')
    mock_repo.create_git_ref.assert_called_once()
    mock_repo.create_pull.assert_called_once()
    assert pr.html_url == 'https://github.com/test/pr'

@patch('src.specifications.update_specifications.Github')
def test_create_pull_request_no_token(mock_github_class):
    """Test creating a pull request without token"""
    # Setup mock to raise BadCredentialsException when None token is used
    mock_github = MagicMock()
    mock_github_class.return_value = mock_github
    mock_github.get_repo.side_effect = BadCredentialsException(401, {'message': 'Bad credentials'})

    with pytest.raises(BadCredentialsException) as exc_info:
        create_pull_request(None, 'Test PR', 'Test body')

    assert 'Bad credentials' in str(exc_info.value)