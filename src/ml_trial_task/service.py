"""Main classes for ml-trial-task"""

from __future__ import annotations

import asyncio
import io
import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp
import torch
from datastreamcorelib.datamessage import PubSubDataMessage
from datastreamservicelib.reqrep import REPMixin, REQMixin
from datastreamservicelib.service import SimpleService
from PIL import Image
from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_V2_Weights,
    fasterrcnn_resnet50_fpn_v2,
)

LOGGER = logging.getLogger(__name__)
# Weights for the model, see the torchvision.models.detection docs for more options
WEIGHTS = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
INFERENCE_THRESHOLD = 0.8


@dataclass
class ImagePredictionService(REPMixin, REQMixin, SimpleService):
    """Service that handles image prediction requests and publishes results.
    Main class for ml-trial-task"""

    model: torch.nn.Module = field(default_factory=torch.nn.Module, repr=False)

    def reload(self) -> None:
        """Load configs, restart sockets"""
        super().reload()

        # Load the detection model (blocking call; if needed, offload to a thread)
        self.model = fasterrcnn_resnet50_fpn_v2(
            weights=WEIGHTS,
            box_score_thresh=INFERENCE_THRESHOLD,
        )
        self.model.eval()
        LOGGER.info("Detection model loaded.")

    async def predict(self, urls: list[str]) -> dict[str, Any]:
        """
        Accepts a list of image URLs, spawns background tasks to process each,
        and immediately returns an acknowledgement.
        """
        if not self.model:
            return {"status": "error", "error": "Model not loaded"}
        for url in urls:
            self.create_task(self.process_image(url, self.model), name=f"processing-{url}")
        return {"status": "processing", "num_images": len(urls)}

    async def process_image(self, url: str, model: torch.nn.Module) -> None:  # pylint: disable=R0914
        """Fetch the image from URL, run detection, and publish results."""
        LOGGER.info("Processing image: {}".format(url))

        # Fetch the image asynchronously using aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"User-Agent": "service"}) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP error: {resp.status}")  # pylint: disable=W0719
                    img_bytes = await resp.read()
        except Exception as e:  # pylint: disable=W0718
            error_result = {"url": url, "error": f"Failed to fetch image: {str(e)}"}
            await self.psmgr.publish_async(PubSubDataMessage(topic="results", data=error_result))
            LOGGER.error("Error fetching {}: {}".format(url, e))
            return

        # Convert bytes to a PIL image
        try:
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as e:  # pylint: disable=W0718
            error_result = {"url": url, "error": f"Image open error: {str(e)}"}
            await self.psmgr.publish_async(PubSubDataMessage(topic="results", data=error_result))
            LOGGER.error("Error processing {}: {}".format(url, e))
            return

        # Preprocess the image using the transforms provided by the weights
        preprocess = WEIGHTS.transforms()
        input_tensor = preprocess(image)  # shape: [3, H, W]

        # Run inference in a thread to avoid blocking the event loop
        try:
            # The model expects a list of tensors
            predictions = await asyncio.to_thread(model, [input_tensor])
        except Exception as e:  # pylint: disable=W0718
            error_result = {"url": url, "error": f"Inference error: {str(e)}"}
            await self.psmgr.publish_async(PubSubDataMessage(topic="results", data=error_result))
            LOGGER.error("Inference error for {}: {}".format(url, e))
            return

        # Extract and convert prediction results
        pred = predictions[0]
        try:
            boxes = pred["boxes"].detach().cpu().numpy().astype(int).tolist()
            labels = pred["labels"].detach().cpu().numpy().tolist()
            labels = [WEIGHTS.meta["categories"][i] for i in labels]
            scores = pred["scores"].detach().cpu().numpy().tolist()
        except Exception as e:  # pylint: disable=W0718
            error_result = {"url": url, "error": f"Result parsing error: {str(e)}"}
            await self.psmgr.publish_async(PubSubDataMessage(topic="results", data=error_result))
            LOGGER.error("Parsing error for {}: {}".format(url, e))
            return

        result = {"url": url, "boxes": boxes, "labels": labels, "scores": scores}
        await self.psmgr.publish_async(PubSubDataMessage(topic="results", data=result))
        LOGGER.info("Published results for {}, labels={}".format(url, labels))
