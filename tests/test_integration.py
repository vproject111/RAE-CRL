import pytest
from typer.testing import CliRunner
from unittest.mock import patch, AsyncMock
from apps.crl.cli.main import app

runner = CliRunner()

def test_cli_init():
    result = runner.invoke(app, ["init", "my-project"])
    assert result.exit_code == 0
    assert "Initialized project context: my-project" in result.stdout

def test_cli_add_command():
    # We mock the method on the instance that is already imported in cli.main
    with patch("apps.crl.cli.main.rae.store_artifact", new_callable=AsyncMock) as mock_store:
        mock_store.return_value = True
        
        result = runner.invoke(app, ["add", "hypothesis", "My Title", "My Desc", "proj1"])
        
        assert result.exit_code == 0
        assert "Stored hypothesis" in result.stdout

def test_cli_query_command():
    with patch("apps.crl.cli.main.rae.query_artifacts", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"content": "Found me", "score": 0.9}]
        
        result = runner.invoke(app, ["query", "something", "proj1"])
        assert result.exit_code == 0
        assert "Found me" in result.stdout
