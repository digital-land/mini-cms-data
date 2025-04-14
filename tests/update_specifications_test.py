import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from ruamel.yaml import YAML
from io import StringIO
from github.GithubException import BadCredentialsException
from src.specifications.update_specifications import (
    get_spec_type,
    order_data,
    update_files_in_branch,
    create_pull_request,
    REPO_NAME
)

# Test data
TEST_SCHEMA = {
    'specifications': {
        'article-4-direction': {
            'order': ['name', 'description', 'fields']
        }
    }
}

TEST_YAML_CONTENT = {
    'data': {
        'description': 'Test description',
        'name': 'Test name',
        'fields': ['field1', 'field2']
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

def test_get_spec_type():
    """Test extracting specification type from filename"""
    assert get_spec_type('data/collections/specifications/article-4-direction.yml') == 'article-4-direction'
    assert get_spec_type('brownfield-land.yml') == 'brownfield-land'

@patch('src.specifications.update_specifications.SCHEMA', TEST_SCHEMA)
def test_order_data():
    """Test ordering data according to schema"""
    # Test with schema matching
    data = {
        'description': 'Test description',
        'name': 'Test name',
        'fields': ['field1', 'field2']
    }
    ordered = order_data(data, 'article-4-direction')
    assert list(ordered.keys()) == ['name', 'description', 'fields']

    # Test with no schema matching
    data = {'test': 'value'}
    ordered = order_data(data, 'non-existent-spec')
    assert ordered == data

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
@patch('ruamel.yaml.YAML.dump')
def test_update_files_in_branch(mock_yaml_dump, mock_yaml_load, mock_open, mock_repo, mock_file):
    """Test updating files in GitHub branch"""
    # Setup mocks
    mock_yaml_load.return_value = TEST_YAML_CONTENT
    mock_repo.get_contents.return_value = mock_file
    mock_repo.update_file.return_value = {'commit': {'sha': 'test_sha'}}

    # Mock StringIO for YAML dump
    buffer = StringIO()
    buffer.write("---\nname: Test name\ndescription: Test description\nfields:\n  - field1\n  - field2\n")
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