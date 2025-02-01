"""Package level tests"""

import asyncio

import tomlkit
import pytest
from datastreamcorelib.datamessage import PubSubDataMessage
from datastreamcorelib.pubsub import Subscription, PubSubMessage


from ml_trial_task import __version__
from ml_trial_task.service import Ml_trial_taskService
from ml_trial_task.defaultconfig import DEFAULT_CONFIG_STR


# pylint: disable=W0621


def test_version() -> None:
    """Make sure version matches expected"""
    assert __version__ == "0.1.0"


def test_defaultconfig() -> None:
    """Test that the default config parses, remember to add any mandatory keys here"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR).unwrap()
    assert "zmq" in parsed
    assert "pub_sockets" in parsed["zmq"]


@pytest.mark.asyncio
async def test_service_starts_and_quits(service_instance: Ml_trial_taskService) -> None:
    """Make sure the service starts and does not immediately die"""
    serv = service_instance
    # Put it as a task in the eventloop (instead of running it as blocking via run_until_complete)
    task = asyncio.create_task(serv.run())
    # Wait a moment and make sure it's still up
    await asyncio.sleep(2)
    assert not task.done()
    # Make sure we have default PUBlish socket
    assert serv.psmgr.default_pub_socket
    assert not serv.psmgr.default_pub_socket.closed
    # Make sure the config got loaded
    assert "zmq" in serv.config
    assert "pub_sockets" in serv.config["zmq"]

    # Tell the service to quit and check the task is done and exitcode is correct
    serv.quit()

    async def wait_for_done() -> None:
        """Wait for the task to be done"""
        nonlocal task
        while True:
            if task.done():
                return
            await asyncio.sleep(0.1)

    await asyncio.wait_for(wait_for_done(), timeout=1.0)
    assert task.done()
    assert task.result() == 0
    assert serv.psmgr.default_pub_socket.closed


@pytest.mark.asyncio
async def test_running_fixture(running_service_instance):  # type: ignore
    """Test the running_instance -fixture"""
    serv = running_service_instance
    await asyncio.sleep(0.1)
    # Make sure we have default PUBlish socket
    assert serv.psmgr.default_pub_socket
    assert not serv.psmgr.default_pub_socket.closed

    # Make sure the heartbeat is sent and received
    hb_received_flag = False

    def hb_callback(sub: Subscription, msg: PubSubMessage) -> None:
        """Callback for the heartbeat subscription below"""
        nonlocal hb_received_flag
        _, _ = sub, msg
        hb_received_flag = True

    sub = Subscription(
        serv.config["zmq"]["pub_sockets"][0],
        "HEARTBEAT",
        hb_callback,
        decoder_class=PubSubDataMessage,
    )
    serv.psmgr.subscribe(sub)

    async def hb_received() -> None:
        """Loop until hb_received_flag is true"""
        nonlocal hb_received_flag
        while not hb_received_flag:
            await asyncio.sleep(0.1)

    await asyncio.wait_for(hb_received(), timeout=5)
    assert hb_received_flag
