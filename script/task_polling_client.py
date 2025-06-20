import asyncio
import logging
import time
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    TaskQueryParams,
    GetTaskRequest,
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

        # Initialize the A2A client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        # Step 1: Send a message and get task ID
        task_id = await send_message_and_get_task_id(client, logger)
        
        if not task_id:
            logger.error("Failed to get task ID from message send")
            return
        
        print(f"Task ID received: {task_id}")
        
        # Step 2: Poll for task status
        await poll_task_status(client, task_id, logger)

async def send_message_and_get_task_id(client: A2AClient, logger: logging.Logger) -> str:
    """Send a message and return the task ID from the response."""
    print("Sending message...")
    
    # Prepare the message payload
    send_message_payload = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": "Hello from A2A client! Tell me a very short story."}],
            "messageId": uuid4().hex,
        }
    }
    
    request = SendMessageRequest(
        id=str(uuid4()),
        method="message/send",
        params=MessageSendParams(**send_message_payload)
    )
    
    try:
        response = await client.send_message(request)
        
        if hasattr(response.root, "error") and response.root.error:
            logger.error("Error sending message: %s", response.root.error.message)
            return None
        
        if hasattr(response.root, "result"):
            result = response.root.result
            
            # Extract task ID from the response
            if hasattr(result, 'taskId') and result.taskId:
                return result.taskId
            elif hasattr(result, 'id') and result.id:
                return result.id
            else:
                logger.warning("No task ID found in response")
                return None
                
    except Exception as e:
        logger.error("Error sending message: %s", e)
        return None

async def poll_task_status(client: A2AClient, task_id: str, logger: logging.Logger):
    """Poll for task status until completion."""
    print(f"Polling task status for task ID: {task_id}")
    
    max_polls = 30  # Maximum number of polls
    poll_interval = 2  # Seconds between polls
    
    for poll_count in range(max_polls):
        try:
            # Create task query parameters
            task_query_params = TaskQueryParams(
                id=task_id,
                historyLength=5  # Request last 5 messages
            )
            
            # Create the request
            request = GetTaskRequest(
                id=str(uuid4()),
                method="tasks/get",
                params=task_query_params
            )
            
            # Send the request
            response = await client.get_task(request)
            
            if hasattr(response.root, "error") and response.root.error:
                logger.error("Error querying task: %s", response.root.error.message)
                break
            
            if hasattr(response.root, "result"):
                task = response.root.result
                status = task.status.state.value
                
                print(f"Poll {poll_count + 1}: Task Status = {status}")
                
                # Display current message if available
                if task.status.message:
                    message_parts = []
                    for part in task.status.message.parts:
                        if hasattr(part.root, 'text'):
                            message_parts.append(part.root.text)
                    if message_parts:
                        print(f"  Current message: {' '.join(message_parts)}")
                
                # Display artifacts if available
                if task.artifacts:
                    print(f"  Artifacts: {len(task.artifacts)} available")
                    for artifact in task.artifacts:
                        print(f"    - {artifact.name} (ID: {artifact.artifactId})")
                
                # Check if task is complete
                if status in ['completed', 'failed', 'cancelled']:
                    print(f"\nTask finished with status: {status}")
                    
                    # Display final history
                    if task.history:
                        print(f"\nFinal Task History ({len(task.history)} messages):")
                        for i, message in enumerate(task.history, 1):
                            role = message.role
                            text_parts = [part.root.text for part in message.parts if hasattr(part.root, 'text')]
                            text = " ".join(text_parts)
                            print(f"  {i}. [{role}]: {text}")
                    
                    break
                
                # Wait before next poll
                if poll_count < max_polls - 1:
                    print(f"  Waiting {poll_interval} seconds before next poll...")
                    await asyncio.sleep(poll_interval)
                    
        except Exception as e:
            logger.error("Error during polling: %s", e)
            break
    
    if poll_count >= max_polls - 1:
        print(f"Reached maximum polls ({max_polls}). Task may still be running.")

if __name__ == "__main__":
    asyncio.run(main()) 