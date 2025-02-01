"""CLI entrypoints for ml-trial-task"""

from typing import Any
import asyncio
import sys
import logging
from pathlib import Path

import click

from datastreamcorelib.logging import init_logging
from ml_trial_task.defaultconfig import DEFAULT_CONFIG_STR
from ml_trial_task import __version__
from ml_trial_task.service import Ml_trial_taskService


LOGGER = logging.getLogger(__name__)


def dump_default_config(ctx: Any, param: Any, value: bool) -> None:  # pylint: disable=W0613
    """Print the default config and exit"""
    if not value:
        return
    click.echo(DEFAULT_CONFIG_STR)
    if ctx:
        ctx.exit()


@click.command()
@click.version_option(version=__version__)
@click.option("-l", "--loglevel", help="Python log level, 10=DEBUG, 20=INFO, 30=WARNING, 40=CRITICAL", default=30)
@click.option("-v", "--verbose", count=True, help="Shorthand for info/debug loglevel (-v/-vv)")
@click.option(
    "--defaultconfig",
    is_flag=True,
    callback=dump_default_config,
    expose_value=False,
    is_eager=True,
    help="Show default config",
)
@click.argument("configfile", type=click.Path(exists=True))
def ml_trial_task_cli(configfile: Path, loglevel: int, verbose: int) -> None:
    """ml trial task"""
    if verbose == 1:
        loglevel = 20
    if verbose >= 2:
        loglevel = 10
    init_logging(loglevel)
    LOGGER.setLevel(loglevel)

    service_instance = Ml_trial_taskService(Path(configfile))

    exitcode = asyncio.get_event_loop().run_until_complete(service_instance.run())
    sys.exit(exitcode)
