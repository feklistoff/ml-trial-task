"""Main classes for ml-trial-task"""

from __future__ import annotations
import asyncio
from typing import cast, Union, Any
from dataclasses import dataclass
import logging


from datastreamcorelib.pubsub import PubSubMessage, Subscription
from datastreamcorelib.datamessage import PubSubDataMessage
from datastreamservicelib.service import SimpleService
from datastreamservicelib.reqrep import REPMixin, REQMixin

LOGGER = logging.getLogger(__name__)


# FIXME: Check this name is good (and PEP8 compliant)
# NOTE: SimpleService does implicit magic, if you don't want that: inherit from BaseService instead
# NOTE: if you need both REPMixin, REQMixin there is also FullService baseclass you can use instead of SimpleService
# here listed separately for example. REPMixin also does a lot of implicit magick, you might not want to leave
# it here unless you need it and definitely go read on how it works.
# If/when you remove these mixins make sure to do something about the related tests too
@dataclass
class Ml_trial_taskService(REPMixin, REQMixin, SimpleService):
    """Main class for ml-trial-task"""

    # This is here for completeness sake, if you do not need it remove it
    async def teardown(self) -> None:
        """Called once by the run method before exiting"""
        # do something or remove this whole method
        await asyncio.sleep(0.001)
        # Remember to let SimpleServices own teardown work too.
        await super().teardown()

    # This is here for completeness sake, if you do not need it remove it
    # Generally you want to use *reload* below for setup type things
    async def setup(self) -> None:
        """Called once by the run method before wating for exitcode to be set"""
        # do something or remove this whole method
        await asyncio.sleep(0.001)
        # Remember to let SimpleServices own setup work too.
        await super().setup()

    async def echo(self, *args: Any) -> Any:
        """return the args, this method is magically found by REPMixin and used to construct the REPly"""
        _ = self
        await asyncio.sleep(0.01)
        return args

    def reload(self) -> None:
        """Load configs, restart sockets"""
        super().reload()
        # Do something

        # Example task sending messages forever (using the inbuilt task tracker helper)
        self.create_task(self.example_message_sender("footopic"), name="looping_sender")
        self.create_task(self.example_request_task(), name="looping_requester")

        # Example subscription for receiving messages (specifically DataMessages)
        sub = Subscription(
            self.config["zmq"]["pub_sockets"][0],  # Listen to our own heartbeat
            "HEARTBEAT",
            self.example_message_callback,
            decoder_class=PubSubDataMessage,
            # This is just an example, don't pass metadata you don't intent to use
            metadata={"somekey": "somevalue"},
        )
        self.psmgr.subscribe_async(sub)

    async def example_request_task(self) -> None:
        """Do a REQuest to the echo method every 1s"""
        try:
            while True:
                # Use our own REP socket to REQuest from since we know that to expect there
                req_uri = self.config["zmq"]["rep_sockets"][0]
                reply = await self.send_command(req_uri, "echo", "plink", "plom", raise_on_insane=True)
                LOGGER.info("Got reply {}".format(reply))
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            # Handle cancellations gracefully
            pass
        return None

    async def example_message_callback(self, sub: Subscription, msg: PubSubMessage) -> None:
        """Callback for the example subscription"""
        # We know it's actually datamessage but the broker deals with the parent type
        msg = cast(PubSubDataMessage, msg)
        LOGGER.info("Got {} (sub.metadata={})".format(msg, sub.metadata))
        # TODO: Do something with the message we got, maybe send some procsessing results out.
        outmsg = PubSubDataMessage(topic="bartopic")
        # Fire-and-forget republish task
        self.create_task(self.psmgr.publish_async(outmsg))

    async def example_message_sender(self, topic: Union[bytes, str]) -> None:
        """Send messages in a loop, the topic is just an example for passing typed arguments"""
        msgno = 0
        try:
            while self.psmgr.default_pub_socket and not self.psmgr.default_pub_socket.closed:
                msgno += 1
                msg = PubSubDataMessage(topic=topic)
                msg.data = {
                    "msgno": msgno,
                }
                LOGGER.debug("Publishing {}".format(msg))
                await self.psmgr.publish_async(msg)
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            # Handle cancellations gracefully
            pass
        return None
