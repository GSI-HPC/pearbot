import os
import subprocess
import sys
import pytest
from unittest.mock import patch

def test_module_import():
    """Test that pearbot module can be imported successfully."""
    try:
        from src import pearbot
        assert True, "pearbot module imported successfully"
    except ImportError as e:
        pytest.fail(f"Failed to import pearbot module: {e}")

def test_help_command():
    """Test that --help command works."""
    # Set dummy environment variables like in CI
    env = os.environ.copy()
    env.update({
        'GITHUB_APP_ID': 'dummy_id',
        'GITHUB_PRIVATE_KEY': 'dummy_key',
        'GITHUB_APP_WEBHOOK_SECRET': 'dummy_secret'
    })

    result = subprocess.run(
        [sys.executable, '-m', 'src.pearbot', '--help'],
        capture_output=True,
        text=True,
        env=env
    )

    assert result.returncode == 0, f"Help command failed with: {result.stderr}"
    assert "Pearbot Code Review" in result.stdout, "Help text should contain 'Pearbot Code Review'"
    assert "--server" in result.stdout, "Help should show --server option"
    assert "--diff" in result.stdout, "Help should show --diff option"

def test_server_startup():
    """Test that server can start (with timeout like in CI)."""
    # Set dummy environment variables like in CI
    env = os.environ.copy()
    env.update({
        'GITHUB_APP_ID': 'dummy_id',
        'GITHUB_PRIVATE_KEY': 'dummy_key',
        'GITHUB_APP_WEBHOOK_SECRET': 'dummy_secret'
    })

    # Use timeout like in CI - expect it to timeout (exit code 124) or succeed (exit code 0)
    result = subprocess.run(
        ['timeout', '5s', sys.executable, '-m', 'src.pearbot', '--server'],
        capture_output=True,
        text=True,
        env=env
    )

    # Exit code 124 means timeout (expected), 0 means success, anything else is failure
    assert result.returncode in [0, 124], f"Server startup failed with exit code {result.returncode}: {result.stderr}"
