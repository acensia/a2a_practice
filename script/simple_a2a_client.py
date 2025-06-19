import asyncio
import logging
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

async def main():
    # URL where your A2A agent server is running
    base_url = "http://localhost:8080"

    # Set up logging (optional)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async with httpx.AsyncClient() as httpx_client:
        # Fetch the agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        logger.info("Fetched agent card: %s", agent_card.model_dump_json(indent=2, exclude_none=True))

        # Initialize the A2A client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        # Prepare the message payload
        send_message_payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Hello from A2A client!"}],
                "messageId": uuid4().hex,
            }
        }
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )

        # Send the message and print the response
        response = await client.send_message(request)
        print("Response:", response.model_dump(mode="json", exclude_none=True))

if __name__ == "__main__":
    asyncio.run(main()) 