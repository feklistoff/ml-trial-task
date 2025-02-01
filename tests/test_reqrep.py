"""test REQ/REP, remove this file if you do not use the mixins"""

import uuid

import pytest

from ml_trial_task.service import Ml_trial_taskService
from .conftest import ExampleREQuester, ExampleREPlier


@pytest.mark.asyncio
async def test_service_reply(
    running_service_instance: Ml_trial_taskService, running_requester_instance: ExampleREQuester
) -> None:
    """Make a request to the echo interface on our service"""
    serv = running_service_instance
    req = running_requester_instance
    req_uri = serv.config["zmq"]["rep_sockets"][0]
    random_str = str(uuid.uuid4())
    reply = await req.send_command(req_uri, "echo", "plink", "plom", random_str, raise_on_insane=True)
    assert reply.topic == b"reply"
    assert not reply.data["failed"]
    response = reply.data["response"]
    assert response[0] == "plink"
    assert response[-1] == random_str


@pytest.mark.asyncio
async def test_service_request(
    running_service_instance: Ml_trial_taskService, running_replier_instance: ExampleREPlier
) -> None:
    """Make a request to the echo interface on our service"""
    serv = running_service_instance
    rep = running_replier_instance
    req_uri = rep.config["zmq"]["rep_sockets"][0]
    random_str = str(uuid.uuid4())
    reply = await serv.send_command(req_uri, "echo", "plink", "plom", random_str, raise_on_insane=True)
    assert reply.topic == b"reply"
    assert not reply.data["failed"]
    response = reply.data["response"]
    assert response[0] == "plink"
    assert response[-1] == random_str
