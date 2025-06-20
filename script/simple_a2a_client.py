import asyncio
import logging
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendStreamingMessageRequest,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)

async def main():
    # URL where your A2A agent server is running
    base_url = "http://192.168.42.78:8000"

    # Set up logging (optional)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async with httpx.AsyncClient() as httpx_client:
        # Fetch the agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        logger.info("Fetched agent card: %s", agent_card.model_dump_json(indent=2, exclude_none=True))

        if not agent_card.capabilities.streaming:
            logger.error("Agent does not support streaming.")
            return

        # Initialize the A2A client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        # Prepare the message payload
        send_message_payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Hello from A2A client! Tell me a very short story."}],
                "messageId": uuid4().hex,
            }
        }
        request = SendStreamingMessageRequest(
            id=str(uuid4()),
            method="message/stream",
            params=MessageSendParams(**send_message_payload)
        )

        # Send the message and handle the stream
        artifacts = {}
        print("Streaming response:")
        try:
            async for response in client.send_message_streaming(request):
                if hasattr(response.root, "error") and response.root.error:
                    logger.error("Received an error: %s", response.root.error.message)
                    break

                if not hasattr(response.root, "result"):
                    logger.warning("Received a response without a result or error: %s", response)
                    continue

                result = response.root.result
                if isinstance(result, TaskArtifactUpdateEvent):
                    artifact_id = result.artifact.artifactId
                    if artifact_id not in artifacts:
                        artifacts[artifact_id] = ""

                    for part in result.artifact.parts:
                        if isinstance(part.root, TextPart):
                            if result.append:
                                artifacts[artifact_id] += part.root.text
                            else:
                                artifacts[artifact_id] = part.root.text
                            print(f"\rArtifact '{artifact_id}': {artifacts[artifact_id]}", end="")

                elif isinstance(result, TaskStatusUpdateEvent):
                    logger.info("Task status update: %s", result.status.state.value)
                    if result.final:
                        print("\nStream finished.")
                        break
        except Exception as e:
            logger.error("An error occurred during streaming: %s", e)

        print("\nFinal artifacts:")
        for artifact_id, content in artifacts.items():
            print(f"- {artifact_id}: {content}")


if __name__ == "__main__":
    asyncio.run(main()) 