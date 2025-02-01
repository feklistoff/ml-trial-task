"""Test fixtures"""

from typing import Any, AsyncGenerator, Generator
import asyncio
from pathlib import Path
import logging
import platform
import random

import tomlkit
import pytest
import pytest_asyncio
from libadvian.testhelpers import nice_tmpdir  # pylint: disable=W0611
from libadvian.logging import init_logging
from datastreamservicelib.reqrep import REPMixin, REQMixin
from datastreamservicelib.service import SimpleService
from datastreamservicelib.compat import asyncio_eventloop_check_policy, asyncio_eventloop_get

from ml_trial_task.defaultconfig import DEFAULT_CONFIG_STR
from ml_trial_task.service import Ml_trial_taskService


# pylint: disable=W0621
init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
asyncio_eventloop_check_policy()


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """override pytest-asyncio default eventloop"""
    loop = asyncio_eventloop_get()
    LOGGER.debug("Yielding {}".format(loop))
    yield loop
    loop.close()


class ExampleREPlier(REPMixin, SimpleService):
    """Implement simple REPly interface, you can use this to mock some other services REPly API"""

    async def echo(self, *args: Any) -> Any:
        """return the args"""
        _ = self
        await asyncio.sleep(0.01)
        return args


class ExampleREQuester(REQMixin, SimpleService):
    """Can be used to test Ml_trial_taskService REP api via REQuests from outside"""


@pytest_asyncio.fixture
async def service_instance(nice_tmpdir: str) -> Ml_trial_taskService:
    """Create a service instance for use with tests"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR).unwrap()
    # On platforms other than windows, do not bind to TCP (and put the sockets into temp paths/ports)
    pub_sock_path = "ipc://" + str(Path(nice_tmpdir) / "ml_trial_task_pub.sock")
    rep_sock_path = "ipc://" + str(Path(nice_tmpdir) / "ml_trial_task_rep.sock")
    if platform.system() == "Windows":
        pub_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
        rep_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
    parsed["zmq"]["pub_sockets"] = [pub_sock_path]
    parsed["zmq"]["rep_sockets"] = [rep_sock_path]
    # Write a testing config file
    configpath = Path(nice_tmpdir) / "ml_trial_task_testing.toml"
    with open(configpath, "wt", encoding="utf-8") as fpntr:
        fpntr.write(tomlkit.dumps(parsed))
    # Instantiate service and return it
    serv = Ml_trial_taskService(configpath)
    return serv


@pytest_asyncio.fixture
async def replier_instance(nice_tmpdir: str) -> ExampleREPlier:
    """Create a replier instance for use with tests"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR).unwrap()
    # Do not bind to TCP socket for testing and use test specific temp directory
    pub_sock_path = "ipc://" + str(Path(nice_tmpdir) / "ml_trial_task_replier_pub.sock")
    rep_sock_path = "ipc://" + str(Path(nice_tmpdir) / "ml_trial_task_replier_rep.sock")
    if platform.system() == "Windows":
        pub_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
        rep_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
    parsed["zmq"]["pub_sockets"] = [pub_sock_path]
    parsed["zmq"]["rep_sockets"] = [rep_sock_path]
    # Write a testing config file
    configpath = Path(nice_tmpdir) / "ml_trial_task_testing_replier.toml"
    with open(configpath, "wt", encoding="utf-8") as fpntr:
        fpntr.write(tomlkit.dumps(parsed))
    # Instantiate service and return it
    serv = ExampleREPlier(configpath)
    return serv


@pytest_asyncio.fixture
async def requester_instance(nice_tmpdir: str) -> ExampleREQuester:
    """Create a requester instance for use with tests"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR).unwrap()
    # Do not bind to TCP socket for testing and use test specific temp directory
    pub_sock_path = "ipc://" + str(Path(nice_tmpdir) / "ml_trial_task_requester_pub.sock")
    if platform.system() == "Windows":
        pub_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
    parsed["zmq"]["pub_sockets"] = [pub_sock_path]
    # Write a testing config file
    configpath = Path(nice_tmpdir) / "ml_trial_task_testing_requester.toml"
    with open(configpath, "wt", encoding="utf-8") as fpntr:
        fpntr.write(tomlkit.dumps(parsed))
    # Instantiate service and return it
    serv = ExampleREQuester(configpath)
    return serv


@pytest_asyncio.fixture
async def running_service_instance(service_instance: Ml_trial_taskService) -> AsyncGenerator[Ml_trial_taskService, None]:
    """Yield a running service instance, shut it down after the test"""
    task = asyncio.create_task(service_instance.run())
    # Yield a moment so setup can do it's thing
    await asyncio.sleep(0.1)

    yield service_instance

    service_instance.quit()

    try:
        await asyncio.wait_for(task, timeout=2)
    except TimeoutError:
        task.cancel()
    finally:
        # Clear alarms and default exception handlers
        Ml_trial_taskService.clear_exit_alarm()
        asyncio.get_event_loop().set_exception_handler(None)


@pytest_asyncio.fixture
async def running_requester_instance(requester_instance: ExampleREQuester) -> AsyncGenerator[ExampleREQuester, None]:
    """Yield a running service instance, shut it down after the test"""
    task = asyncio.create_task(requester_instance.run())
    # Yield a moment so setup can do it's thing
    await asyncio.sleep(0.1)

    yield requester_instance

    requester_instance.quit()

    try:
        await asyncio.wait_for(task, timeout=2)
    except TimeoutError:
        task.cancel()
    finally:
        # Clear alarms and default exception handlers
        ExampleREQuester.clear_exit_alarm()
        asyncio.get_event_loop().set_exception_handler(None)


@pytest_asyncio.fixture
async def running_replier_instance(replier_instance: ExampleREPlier) -> AsyncGenerator[ExampleREPlier, None]:
    """Yield a running service instance, shut it down after the test"""
    task = asyncio.create_task(replier_instance.run())
    # Yield a moment so setup can do it's thing
    await asyncio.sleep(0.1)

    yield replier_instance

    replier_instance.quit()

    try:
        await asyncio.wait_for(task, timeout=2)
    except TimeoutError:
        task.cancel()
    finally:
        # Clear alarms and default exception handlers
        ExampleREPlier.clear_exit_alarm()
        asyncio.get_event_loop().set_exception_handler(None)
