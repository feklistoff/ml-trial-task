"""Test CLI scripts"""

import asyncio
from pathlib import Path
from typing import AnyStr

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner
from datastreamcorelib.binpackers import ensure_str
from ml_trial_task import __version__
from ml_trial_task.console import cli, dump_default_config
from ml_trial_task.defaultconfig import DEFAULT_CONFIG_STR

# A minimal dummy config that satisfies the CLI
DUMMY_CONFIG = """
[zmq]
rep_sockets = ["tcp://127.0.0.1:5555"]
pub_sockets = ["tcp://127.0.0.1:5556"]
"""


class DummyService:  # pylint: disable=R0903
    """A dummy service to use for testing the "service" command."""

    async def run(self) -> int:  # pylint: disable=C0116
        return 0


@pytest.fixture
def config_file(tmp_path: Path) -> str:
    """Fixture to create a temporary config file."""
    config = tmp_path / "config.toml"
    config.write_text(DUMMY_CONFIG)
    return str(config)


def test_run_predict_no_urls(config_file: str) -> None:  # pylint: disable=W0621
    """Test that if neither --urls nor --csv is provided the predict command exits with a proper message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["predict", config_file])
    assert "No URLs provided" in result.output


def test_run_service_success(monkeypatch: MonkeyPatch, config_file: str) -> None:  # pylint: disable=W0621
    """Test the service command by monkeypatching ImagePredictionService to return 0."""
    # Replace ImagePredictionService with a dummy that returns exit code 0
    monkeypatch.setattr("ml_trial_task.console.ImagePredictionService", lambda cfg: DummyService())
    runner = CliRunner()
    result = runner.invoke(cli, ["service", config_file], catch_exceptions=False)
    # The CLI command should exit with code 0.
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_run_predict_with_urls(tmp_path: Path) -> None:
    """Test the predict command when providing URLs."""
    # Create a temporary config file.
    config = tmp_path / "config.toml"
    config.write_text(DUMMY_CONFIG)
    config_file_path = str(config)

    runner = CliRunner()
    # Pass a single URL using the --urls option.
    result = runner.invoke(cli, ["predict", "--urls", "http://example.com/image.jpg", config_file_path])
    assert "URLs provided" in result.output


def test_default_config_func(capsys: pytest.CaptureFixture[AnyStr]) -> None:
    """Make sure the default config is/is not dumped"""
    dump_default_config(None, None, True)
    captured = capsys.readouterr()
    assert captured.out.strip() == DEFAULT_CONFIG_STR.strip()
    dump_default_config(None, None, False)
    captured = capsys.readouterr()
    assert captured.out.strip() == ""


@pytest.mark.asyncio
async def test_default_config_cli() -> None:
    """Test the CLI parsing for default config dumping works"""
    cmd = "ml_trial_task --defaultconfig"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out = await asyncio.wait_for(process.communicate(), 10)
    # Demand clean exit
    assert process.returncode == 0
    # Check output
    assert ensure_str(out[0]).strip() == DEFAULT_CONFIG_STR.strip()


@pytest.mark.asyncio
async def test_version_cli() -> None:
    """Test the CLI parsing for default config dumping works"""
    cmd = "ml_trial_task --version"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out = await asyncio.wait_for(process.communicate(), 10)
    # Demand clean exit
    assert process.returncode == 0
    # Check output
    assert ensure_str(out[0]).strip().endswith(__version__)
