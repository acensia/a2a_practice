import asyncio
import logging
import time
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendStreamingMessageRequest,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
    TaskQueryParams,
    GetTaskRequest,
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

        # Initialize timing variables
        request_start_time = time.time()
        first_response_time = None
        artifact_times = {}
        stream_end_time = None
        
        # Send the message and handle the stream
        artifacts = {}
        task_id = None
        print("Streaming response:")
        try:
            async for response in client.send_message_streaming(request):
                current_time = time.time()
                
                if hasattr(response.root, "error") and response.root.error:
                    logger.error("Received an error: %s", response.root.error.message)
                    break

                if not hasattr(response.root, "result"):
                    logger.warning("Received a response without a result or error: %s", response)
                    continue

                result = response.root.result
                
                # Capture task ID from TaskStatusUpdateEvent
                if isinstance(result, TaskStatusUpdateEvent):
                    if hasattr(result, 'taskId') and result.taskId:
                        task_id = result.taskId
                        logger.info("Task ID captured: %s", task_id)
                    
                    logger.info("Task status update: %s", result.status.state.value)
                    if result.final:
                        stream_end_time = current_time
                        print("\nStream finished.")
                        break
                
                elif isinstance(result, TaskArtifactUpdateEvent):
                    # Capture task ID from TaskArtifactUpdateEvent if not already captured
                    if not task_id and hasattr(result, 'taskId') and result.taskId:
                        task_id = result.taskId
                        logger.info("Task ID captured from artifact update: %s", task_id)
                    
                    artifact_id = result.artifact.artifactId
                    
                    # Record first response time
                    if first_response_time is None:
                        first_response_time = current_time
                        first_response_duration = first_response_time - request_start_time
                        print(f"\n⏱️  First response received in: {first_response_duration:.3f} seconds")
                    
                    # Record artifact timing
                    if artifact_id not in artifact_times:
                        artifact_times[artifact_id] = current_time
                        artifact_duration = current_time - request_start_time
                        print(f"\n📦 Artifact '{artifact_id}' first received in: {artifact_duration:.3f} seconds")
                    
                    if artifact_id not in artifacts:
                        artifacts[artifact_id] = ""

                    for part in result.artifact.parts:
                        if isinstance(part.root, TextPart):
                            if result.append:
                                artifacts[artifact_id] += part.root.text
                            else:
                                artifacts[artifact_id] = part.root.text
                            print(f"\rArtifact '{artifact_id}': {artifacts[artifact_id]}", end="")
                            
        except Exception as e:
            logger.error("An error occurred during streaming: %s", e)
            stream_end_time = time.time()

        # Calculate and display timing results
        if stream_end_time is None:
            stream_end_time = time.time()
        
        total_duration = stream_end_time - request_start_time
        
        print("\n" + "="*50)
        print("⏱️  TIMING RESULTS")
        print("="*50)
        print(f"Total request duration: {total_duration:.3f} seconds")
        
        if first_response_time:
            print(f"Time to first response: {first_response_duration:.3f} seconds")
        
        if artifact_times:
            print(f"\nArtifact timing breakdown:")
            for artifact_id, artifact_time in artifact_times.items():
                artifact_duration = artifact_time - request_start_time
                print(f"  - {artifact_id}: {artifact_duration:.3f} seconds")
        
        print("="*50)

        print("\nFinal artifacts:")
        for artifact_id, content in artifacts.items():
            print(f"- {artifact_id}: {content}")
        
        # If we captured a task ID, demonstrate task querying
        if task_id:
            print(f"\nTask ID: {task_id}")
            await query_task_status(client, task_id, logger)
        else:
            print("\nNo task ID captured from streaming response.")

async def query_task_status(client: A2AClient, task_id: str, logger: logging.Logger):
    """Query the status of a specific task using the task ID."""
    print(f"\nQuerying task status for task ID: {task_id}")
    
    try:
        # Create task query parameters
        task_query_params = TaskQueryParams(
            id=task_id,
            historyLength=10  # Request last 10 messages
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
            return
        
        if hasattr(response.root, "result"):
            task = response.root.result
            print(f"Task Status: {task.status.state.value}")
            print(f"Context ID: {task.contextId}")
            
            if task.history:
                print(f"\nTask History ({len(task.history)} messages):")
                for i, message in enumerate(task.history[-5:], 1):  # Show last 5 messages
                    role = message.role
                    text_parts = [part.root.text for part in message.parts if hasattr(part.root, 'text')]
                    text = " ".join(text_parts)
                    print(f"  {i}. [{role}]: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            if task.artifacts:
                print(f"\nTask Artifacts ({len(task.artifacts)} artifacts):")
                for artifact in task.artifacts:
                    print(f"  - {artifact.name} (ID: {artifact.artifactId})")
                    
    except Exception as e:
        logger.error("Error querying task status: %s", e)

if __name__ == "__main__":
    asyncio.run(main()) 