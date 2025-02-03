"""CLI entrypoints for ml-trial-task"""

import asyncio
import csv
import logging
import sys
from pathlib import Path
from typing import Any, cast

import click
import toml
from datastreamcorelib.datamessage import PubSubDataMessage
from datastreamcorelib.logging import init_logging
from datastreamcorelib.pubsub import PubSubMessage, Subscription
from datastreamservicelib.reqrep import REQMixin
from datastreamservicelib.zmqwrappers import PubSubManager, SocketHandler

from ml_trial_task import __version__
from ml_trial_task.defaultconfig import DEFAULT_CONFIG_STR
from ml_trial_task.service import ImagePredictionService

LOGGER = logging.getLogger(__name__)


def dump_default_config(ctx: Any, param: Any, value: bool) -> None:  # pylint: disable=W0613
    """Print the default config and exit"""
    if not value:
        return
    click.echo(DEFAULT_CONFIG_STR)
    if ctx:
        ctx.exit()


@click.group()
def cli() -> None:
    """Main command group for ml-trial-task."""


@cli.command(name="service")
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
def run_service(configfile: Path, loglevel: int, verbose: int) -> None:
    """Run the ml-trial-task service."""
    if verbose == 1:
        loglevel = 20
    if verbose >= 2:
        loglevel = 10
    init_logging(loglevel)
    LOGGER.setLevel(loglevel)

    service_instance = ImagePredictionService(Path(configfile))
    exitcode = asyncio.get_event_loop().run_until_complete(service_instance.run())
    sys.exit(exitcode)


@cli.command(name="predict")
@click.option(
    "-u",
    "--urls",
    help="Comma-separated list of image URLs to process.",
    default="",
)
@click.option(
    "-c",
    "--csv",
    "csv_file",
    type=click.Path(exists=True),
    help="CSV file with image URLs (assumes URL is in the first column)",
)
@click.argument("configfile", type=click.Path(exists=True))
def run_predict(configfile: Path, urls: str, csv_file: str) -> None:
    """
    Send a predict command to a running service and listen for published results.
    The service will publish detection results on the "results" topic.
    """
    url_list: list[str] = []
    if urls:
        url_list.extend([u.strip() for u in urls.split(",") if u.strip()])
    if csv_file:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            # Skip the header row
            next(reader)
            for row in reader:
                if row:
                    url_list.append(row[0])
    if not url_list:
        click.echo("No URLs provided. Use --urls or --csv to supply image URLs.")
        return

    click.echo(f"URLs provided: {url_list}\n")
    expected_count = len(url_list)

    async def predict_and_listen() -> None:
        nonlocal expected_count

        # Send the predict command over the REP socket.
        requester = REQMixin(Path(configfile))
        requester.config = toml.load(Path(configfile))
        response = await requester.send_command(requester.config["zmq"]["rep_sockets"][0], "predict", url_list)
        click.echo(f"Predict command response: {response}\n")

        # Extract the expected number of results from the response.
        received_count = 0
        done_event = asyncio.Event()

        async def message_callback(sub: Subscription, msg: PubSubMessage) -> None:  # pylint: disable=W0613
            """Callback for subscription. Just log the message."""

            nonlocal received_count
            # We know it's actually datamessage but the broker deals with the parent type
            msg = cast(PubSubDataMessage, msg)
            click.echo(f"Received: {msg}")
            received_count += 1
            if received_count >= expected_count:
                done_event.set()

        # Subscribe to the "results" topic on the PUB socket.
        subscriber = Subscription(
            requester.config["zmq"]["pub_sockets"][0],
            "results",
            message_callback,
            decoder_class=PubSubDataMessage,
        )
        pub_sub_manager = PubSubManager(SocketHandler)
        pub_sub_manager.subscribe_async(subscriber)
        click.echo("Subscribed and waiting for results\n")

        # Wait until all expected messages are received.
        await done_event.wait()
        click.echo("All results received; exiting.")

    asyncio.run(predict_and_listen())


if __name__ == "__main__":
    cli()
