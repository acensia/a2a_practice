# A2A Client Scripts with Task ID Support

This directory contains enhanced A2A client scripts that demonstrate how to work with task IDs for better task management and monitoring.

## Scripts Overview

### 1. `simple_a2a_client.py` (Enhanced)
- **Purpose**: Streaming client with task ID capture and querying
- **Features**:
  - Captures task ID from streaming responses
  - Automatically queries task status after streaming completes
  - Displays task history and artifacts
  - Enhanced error handling

### 2. `task_polling_client.py` (New)
- **Purpose**: Demonstrates polling-based task monitoring
- **Features**:
  - Sends message and gets task ID
  - Polls task status until completion
  - Alternative to streaming for long-running tasks
  - Configurable polling intervals and limits

### 3. `task_query_example.py` (New)
- **Purpose**: Query existing tasks by their ID
- **Features**:
  - Command-line interface for task queries
  - Detailed task information display
  - Useful for checking status of previously created tasks

## Usage Examples

### Running the Enhanced Streaming Client
```bash
python simple_a2a_client.py
```

This will:
1. Send a message to the A2A agent
2. Stream the response in real-time
3. Capture the task ID from the response
4. Query the final task status and display history

### Running the Polling Client
```bash
python task_polling_client.py
```

This will:
1. Send a message and get the task ID
2. Poll the task status every 2 seconds
3. Display progress updates
4. Show final results when complete

### Querying a Specific Task
```bash
python task_query_example.py <task_id>
```

Example:
```bash
python task_query_example.py 3f36680c-7f37-4a5f-945e-d78981fafd36
```

You can also specify a custom server URL:
```bash
python task_query_example.py 3f36680c-7f37-4a5f-945e-d78981fafd36 http://localhost:8080
```

## Key Features Added

### Task ID Capture
- Automatically captures task IDs from streaming responses
- Extracts task ID from both `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent`
- Logs task ID for debugging and reference

### Task Querying
- Uses `TaskQueryParams` to specify task ID and history length
- Implements `tasks/get` method for task status queries
- Displays comprehensive task information including:
  - Task status and timestamp
  - Message history
  - Artifacts and their content
  - Metadata

### Polling Mechanism
- Configurable polling intervals (default: 2 seconds)
- Maximum poll limits to prevent infinite loops
- Status-based completion detection
- Real-time progress updates

### Error Handling
- Graceful handling of missing task IDs
- Network error recovery
- Invalid task ID detection
- Comprehensive logging

## Configuration

### Server URL
All scripts use `http://192.168.42.78:8000` as the default server URL. You can modify this in the script or use command-line arguments where supported.

### Polling Settings
In `task_polling_client.py`, you can adjust:
- `max_polls`: Maximum number of polling attempts (default: 30)
- `poll_interval`: Seconds between polls (default: 2)

### History Length
In task queries, you can specify how many recent messages to retrieve:
- `historyLength=10` for recent messages
- `historyLength=20` for more detailed history

## A2A Protocol Integration

These scripts demonstrate the following A2A protocol features:

1. **`message/stream`**: Real-time streaming with task ID capture
2. **`message/send`**: Simple message sending with task ID response
3. **`tasks/get`**: Task status querying with `TaskQueryParams`
4. **Task Status Monitoring**: Tracking task state changes
5. **Artifact Handling**: Processing and displaying task artifacts

## Troubleshooting

### Common Issues

1. **No Task ID Captured**
   - Check if the server supports task ID in responses
   - Verify the response format matches expected structure

2. **Connection Errors**
   - Ensure the A2A server is running
   - Check the server URL configuration
   - Verify network connectivity

3. **Task Not Found**
   - Verify the task ID is correct
   - Check if the task has been cleaned up by the server
   - Ensure the task ID format is valid

### Debug Mode
Enable debug logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

- `a2a-sdk>=0.2.8`
- `httpx` (for HTTP client)
- `asyncio` (for async operations)
- `uuid` (for request ID generation)

## Next Steps

Consider implementing:
1. **Push Notifications**: Webhook-based task status updates
2. **Task Cancellation**: Ability to cancel running tasks
3. **Batch Operations**: Multiple task management
4. **Persistent Storage**: Save task IDs for later reference
5. **GUI Interface**: Web-based task monitoring dashboard 