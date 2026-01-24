from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from apps.crl.cli.main import app

runner = CliRunner()


def test_cli_init():
    result = runner.invoke(app, ["init", "my-project"])
    assert result.exit_code == 0
    assert "Initialized project context" in result.stdout


def test_cli_add_command_success():
    # Mocking the RAEClient instance method used in the CLI
    with patch("apps.crl.cli.main.rae") as mock_rae:
        mock_rae.store_artifact = AsyncMock(return_value=True)

        result = runner.invoke(
            app, ["add", "hypothesis", "Flat Earth", "Needs checking", "p1"]
        )

        assert result.exit_code == 0
        assert "Stored hypothesis" in result.stdout
        mock_rae.store_artifact.assert_called_once()


def test_cli_add_command_failure():
    with patch("apps.crl.cli.main.rae") as mock_rae:
        mock_rae.store_artifact = AsyncMock(return_value=False)

        result = runner.invoke(app, ["add", "hypothesis", "Bad", "Desc", "p1"])

        assert result.exit_code == 0
        assert "Failed to store artifact" in result.stdout


def test_cli_query_command():
    with patch("apps.crl.cli.main.rae") as mock_rae:
        mock_rae.query_artifacts = AsyncMock(
            return_value=[{"content": "Evidence A", "score": 0.95}]
        )

        result = runner.invoke(app, ["query", "evidence", "p1"])

        assert result.exit_code == 0
        assert "Evidence A" in result.stdout
        assert "0.95" in result.stdout
