import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PlainScalarString
from io import StringIO
from github.GithubException import BadCredentialsException
from src.specifications.update_specifications import (
    order_data,
    order_dataset,
    order_field,
    get_data_order,
    get_dataset_field_order,
    get_field_property_order,
    update_files_in_branch,
    create_pull_request,
    REPO_NAME
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
                    {'field': 'field1', 'description': 'Field 1', 'guidance': 'Guidance 1'},
                    {'field': 'field2', 'description': 'Field 2', 'guidance': 'Guidance 2'}
                ]
            }
        ]
    }
}

# Mock config for testing
MOCK_CONFIG = {
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
                {
                    'id': 'datasets',
                    'fields': [
                        {'id': 'dataset'},
                        {'id': 'name'},
                        {
                            'id': 'fields',
                            'fields': [
                                {'id': 'field'},
                                {'id': 'description'},
                                {'id': 'guidance'}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
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
def test_get_data_order(mock_yaml_load, mock_open):
    """Test getting data order from config"""
    mock_yaml_load.return_value = MOCK_CONFIG

    order = get_data_order()
    expected_order = ['specification', 'name', 'plural', 'specification-status', 'start-date',
                     'end-date', 'entry-date', 'github-discussion', 'version', 'datasets']
    assert order == expected_order

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_get_dataset_field_order(mock_yaml_load, mock_open):
    """Test getting dataset field order from config"""
    mock_yaml_load.return_value = MOCK_CONFIG

    order = get_dataset_field_order()
    expected_order = ['dataset', 'name', 'fields']
    assert order == expected_order

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_get_field_property_order(mock_yaml_load, mock_open):
    """Test getting field property order from config"""
    mock_yaml_load.return_value = MOCK_CONFIG

    order = get_field_property_order()
    expected_order = ['field', 'description', 'guidance']
    assert order == expected_order

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data_strict_ordering(mock_yaml_load, mock_open):
    """Test that order_data produces strictly ordered output"""
    mock_yaml_load.return_value = MOCK_CONFIG

    # Test data with fields in random order
    data = {
        'version': '1.0.0',
        'name': 'Test name',
        'specification': 'test-spec',
        'datasets': [],
        'entry-date': '2024-01-01',
        'github-discussion': '123',
        'plural': 'Test names',
        'specification-status': 'candidate-standard',
        'start-date': '2024-01-01',
        'end-date': ''
    }

    ordered = order_data(data)

    # Verify strict ordering
    expected_order = ['specification', 'name', 'plural', 'specification-status', 'start-date',
                     'end-date', 'entry-date', 'github-discussion', 'version', 'datasets']
    actual_order = list(ordered.keys())
    assert actual_order == expected_order

    # Verify all keys are PlainScalarString
    for key in ordered.keys():
        assert isinstance(key, PlainScalarString)

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_dataset_strict_ordering(mock_yaml_load, mock_open):
    """Test that order_dataset produces strictly ordered output"""
    mock_yaml_load.return_value = MOCK_CONFIG

    # Test dataset with fields in random order
    dataset = {
        'name': 'Test dataset',
        'dataset': 'test-dataset',
        'fields': []
    }

    ordered = order_dataset(dataset)

    # Verify strict ordering
    expected_order = ['dataset', 'name', 'fields']
    actual_order = list(ordered.keys())
    assert actual_order == expected_order

    # Verify all keys are PlainScalarString
    for key in ordered.keys():
        assert isinstance(key, PlainScalarString)

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_field_strict_ordering(mock_yaml_load, mock_open):
    """Test that order_field produces strictly ordered output"""
    mock_yaml_load.return_value = MOCK_CONFIG

    # Test field with properties in random order
    field = {
        'description': 'Field description',
        'field': 'field1',
        'guidance': 'Field guidance'
    }

    ordered = order_field(field)

    # Verify strict ordering
    expected_order = ['field', 'description', 'guidance']
    actual_order = list(ordered.keys())
    assert actual_order == expected_order

    # Verify all keys are PlainScalarString
    for key in ordered.keys():
        assert isinstance(key, PlainScalarString)

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data_with_nested_datasets(mock_yaml_load, mock_open):
    """Test ordering data with nested datasets and fields"""
    mock_yaml_load.return_value = MOCK_CONFIG

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
        'datasets': [
            {
                'name': 'Test dataset',
                'dataset': 'test-dataset',
                'fields': [
                    {
                        'description': 'Field 1 description',
                        'field': 'field1',
                        'guidance': 'Field 1 guidance'
                    },
                    {
                        'guidance': 'Field 2 guidance',
                        'field': 'field2',
                        'description': 'Field 2 description'
                    }
                ]
            }
        ]
    }

    ordered = order_data(data)

    # Verify top-level ordering
    expected_top_order = ['specification', 'name', 'plural', 'specification-status', 'start-date',
                         'end-date', 'entry-date', 'github-discussion', 'version', 'datasets']
    assert list(ordered.keys()) == expected_top_order

    # Verify dataset ordering
    first_dataset = ordered['datasets'][0]
    expected_dataset_order = ['dataset', 'name', 'fields']
    assert list(first_dataset.keys()) == expected_dataset_order

    # Verify field ordering
    first_field = first_dataset['fields'][0]
    expected_field_order = ['field', 'description', 'guidance']
    assert list(first_field.keys()) == expected_field_order

    second_field = first_dataset['fields'][1]
    assert list(second_field.keys()) == expected_field_order

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data_missing_fields(mock_yaml_load, mock_open):
    """Test ordering data with missing fields"""
    mock_yaml_load.return_value = MOCK_CONFIG

    # Test with only some fields present
    data = {
        'name': 'Test name',
        'version': '1.0.0',
        'specification': 'test-spec'
    }

    ordered = order_data(data)

    # Should only include present fields in correct order
    expected_order = ['specification', 'name', 'version']
    assert list(ordered.keys()) == expected_order

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data_extra_fields_ignored(mock_yaml_load, mock_open):
    """Test that extra fields not in schema are ignored"""
    mock_yaml_load.return_value = MOCK_CONFIG

    data = {
        'specification': 'test-spec',
        'name': 'Test name',
        'extra_field': 'should be ignored',
        'another_extra': 'should also be ignored',
        'version': '1.0.0'
    }

    ordered = order_data(data)

    # Should only include schema fields in correct order
    expected_order = ['specification', 'name', 'version']
    assert list(ordered.keys()) == expected_order
    assert 'extra_field' not in ordered
    assert 'another_extra' not in ordered

def test_export_format_validation():
    """Test that the export format matches expected structure"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096

    # Test data that should produce the expected format
    test_data = {
        'specification': 'article-4-direction',
        'name': 'Article 4 direction',
        'plural': 'article 4 directions',
        'specification-status': 'candidate-standard',
        'start-date': '',
        'end-date': '',
        'entry-date': '2023-09-11',
        'github-discussion': 30,
        'version': '1.3.3',
        'datasets': [
            {
                'dataset': 'article-4-direction',
                'name': 'article 4 direction',
                'fields': [
                    {
                        'field': 'reference',
                        'description': 'the reference for the article 4 direction',
                        'guidance': 'A reference or ID for each article 4 direction'
                    }
                ]
            }
        ]
    }

    # Convert to YAML
    buffer = StringIO()
    yaml.dump(test_data, buffer)
    yaml_output = buffer.getvalue().strip()

    # Add frontmatter markers
    final_output = f"---\n{yaml_output}\n"

    # Verify the structure
    assert final_output.startswith("---\n")
    assert final_output.endswith("\n")

    # Verify key fields are present and in order
    lines = yaml_output.split('\n')
    assert 'specification: article-4-direction' in lines
    assert 'name: Article 4 direction' in lines
    assert 'plural: article 4 directions' in lines
    assert 'specification-status: candidate-standard' in lines
    assert 'start-date: \'\'' in lines
    assert 'end-date: \'\'' in lines
    assert 'entry-date: \'2023-09-11\'' in lines
    assert 'github-discussion: 30' in lines
    assert 'version: 1.3.3' in lines
    assert 'datasets:' in lines

    # Verify datasets structure
    assert '  - dataset: article-4-direction' in lines
    assert '    name: article 4 direction' in lines
    assert '    fields:' in lines

    # Verify fields structure
    assert '      - field: reference' in lines
    assert '        description: the reference for the article 4 direction' in lines
    assert '        guidance: A reference or ID for each article 4 direction' in lines

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data_with_empty_datasets(mock_yaml_load, mock_open):
    """Test ordering data with empty datasets array"""
    mock_yaml_load.return_value = MOCK_CONFIG

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
        'datasets': []
    }

    ordered = order_data(data)

    # Should handle empty datasets array correctly
    assert 'datasets' in ordered
    assert ordered['datasets'] == []

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data_with_empty_fields(mock_yaml_load, mock_open):
    """Test ordering data with empty fields array"""
    mock_yaml_load.return_value = MOCK_CONFIG

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
        'datasets': [
            {
                'dataset': 'test-dataset',
                'name': 'Test dataset',
                'fields': []
            }
        ]
    }

    ordered = order_data(data)

    # Should handle empty fields array correctly
    first_dataset = ordered['datasets'][0]
    assert 'fields' in first_dataset
    assert first_dataset['fields'] == []

@patch('builtins.open', new_callable=MagicMock)
@patch('ruamel.yaml.YAML.load')
def test_order_data(mock_yaml_load, mock_open):
    """Test ordering data according to schema"""
    # Mock the config file content
    mock_yaml_load.return_value = MOCK_CONFIG

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
        'datasets': [
            {
                'dataset': 'test-dataset',
                'name': 'Test dataset',
                'fields': [
                    {'field': 'field1', 'description': 'Field 1'},
                    {'field': 'field2', 'description': 'Field 2'}
                ]
            }
        ],
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
    config_yaml = MOCK_CONFIG

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