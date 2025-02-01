"""Test CLI scripts"""

from typing import AnyStr
import asyncio

import pytest
from datastreamcorelib.binpackers import ensure_str

from ml_trial_task import __version__
from ml_trial_task.console import dump_default_config
from ml_trial_task.defaultconfig import DEFAULT_CONFIG_STR


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
