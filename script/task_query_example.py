import asyncio
import logging
import sys
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    TaskQueryParams,
    GetTaskRequest,
)

async def query_task_by_id(task_id: str, base_url: str = "http://192.168.42.78:8000"):
    """
    Query a specific task by its ID.
    
    Args:
        task_id: The ID of the task to query
        base_url: The base URL of the A2A agent server
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async with httpx.AsyncClient() as httpx_client:
        try:
            # Fetch the agent card
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            logger.info("Fetched agent card successfully")

            # Initialize the A2A client
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

            # Query the task
            await query_task_status(client, task_id, logger)
            
        except Exception as e:
            logger.error("Failed to connect to A2A server: %s", e)
            print(f"Error: {e}")
            return False
    
    return True

async def query_task_status(client: A2AClient, task_id: str, logger: logging.Logger):
    """Query the status of a specific task using the task ID."""
    print(f"Querying task status for task ID: {task_id}")
    
    try:
        # Create task query parameters with different history lengths
        task_query_params = TaskQueryParams(
            id=task_id,
            historyLength=20  # Request last 20 messages for detailed history
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
            print(f"Error: {response.root.error.message}")
            return
        
        if hasattr(response.root, "result"):
            task = response.root.result
            
            # Display task information
            print("\n" + "="*60)
            print("TASK INFORMATION")
            print("="*60)
            print(f"Task ID: {task.id}")
            print(f"Context ID: {task.contextId}")
            print(f"Status: {task.status.state.value}")
            print(f"Timestamp: {task.status.timestamp}")
            
            # Display current message if available
            if task.status.message:
                print(f"\nCurrent Message:")
                print("-" * 30)
                message_parts = []
                for part in task.status.message.parts:
                    if hasattr(part.root, 'text'):
                        message_parts.append(part.root.text)
                if message_parts:
                    print(" ".join(message_parts))
            
            # Display task history
            if task.history:
                print(f"\nTask History ({len(task.history)} messages):")
                print("-" * 30)
                for i, message in enumerate(task.history, 1):
                    role = message.role
                    text_parts = [part.root.text for part in message.parts if hasattr(part.root, 'text')]
                    text = " ".join(text_parts)
                    print(f"{i:2d}. [{role:6s}]: {text}")
            
            # Display artifacts
            if task.artifacts:
                print(f"\nArtifacts ({len(task.artifacts)}):")
                print("-" * 30)
                for i, artifact in enumerate(task.artifacts, 1):
                    print(f"{i}. Name: {artifact.name}")
                    print(f"   ID: {artifact.artifactId}")
                    if artifact.parts:
                        print(f"   Parts: {len(artifact.parts)}")
                        for j, part in enumerate(artifact.parts, 1):
                            if hasattr(part.root, 'text'):
                                print(f"     {j}. Text: {part.root.text[:100]}{'...' if len(part.root.text) > 100 else ''}")
                    print()
            
            # Display metadata if available
            if task.metadata:
                print(f"\nMetadata:")
                print("-" * 30)
                for key, value in task.metadata.items():
                    print(f"{key}: {value}")
            
            print("="*60)
            
        else:
            print("No result found in response")
            
    except Exception as e:
        logger.error("Error querying task status: %s", e)
        print(f"Error: {e}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python task_query_example.py <task_id> [base_url]")
        print("Example: python task_query_example.py 3f36680c-7f37-4a5f-945e-d78981fafd36")
        print("Example: python task_query_example.py 3f36680c-7f37-4a5f-945e-d78981fafd36 http://localhost:8080")
        return
    
    task_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://192.168.42.78:8000"
    
    print(f"Querying task ID: {task_id}")
    print(f"Server URL: {base_url}")
    
    asyncio.run(query_task_by_id(task_id, base_url))

if __name__ == "__main__":
    main() 