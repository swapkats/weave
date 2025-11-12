# Weave Unified Tool System

## Overview

The Weave tool system has been unified to provide consistent tool execution across all executors:

- **Main Executor** (`runtime/executor.py`)
- **LLM Executor** (`runtime/llm_executor.py`)
- **OpenAI API Server** (`api/openai_server.py`)

All three execution paths now use the same **ToolExecutor** class, ensuring consistent behavior and tool availability.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Tool Executor                         │
│  (tools/executor.py)                                    │
│                                                         │
│  - Loads comprehensive tools                           │
│  - Loads built-in tools                                │
│  - Loads MCP tools                                     │
│  - Manages tool registry                               │
│  - Executes tools with unified interface               │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼─────┐
    │  Main   │    │   LLM   │    │  OpenAI  │
    │Executor │    │Executor │    │  Server  │
    └─────────┘    └─────────┘    └──────────┘
```

## Comprehensive Tools

The system provides 13 comprehensive tools in `tools/comprehensive.py`:

### File Operations

1. **FindFiles** - Find files matching a glob pattern
   - Pattern matching with recursive search
   - Supports glob patterns like `*.py`, `**/*.ts`
   - Configurable max results

2. **ReadFile** - Read file contents
   - UTF-8 encoding by default
   - Size limits for safety
   - Error handling for missing files

3. **ReadFolder** - List directory contents
   - Pattern filtering
   - Recursive listing option
   - Separates files and directories

4. **ReadManyFiles** - Read multiple files at once
   - Batch file reading
   - Per-file size limits
   - Error tracking for failed reads

5. **WriteFile** - Write content to files
   - Auto-create parent directories
   - Append mode support
   - Atomic writes

6. **SearchText** - Search for text patterns in files
   - Regex pattern support
   - Context lines
   - File pattern filtering
   - Recursive search

### Shell Operations

7. **Shell** - Execute shell commands
   - Timeout support
   - Working directory configuration
   - Environment variable support
   - Captures stdout/stderr

### Web Operations

8. **WebFetch** - Fetch content from URLs
   - All HTTP methods (GET, POST, PUT, DELETE, PATCH)
   - Custom headers
   - Request body support
   - Timeout configuration

9. **GoogleSearch** - Search Google
   - Configurable result count
   - Language support
   - Uses googlesearch-python library

### Memory Operations

10. **SaveMemory** - Save values to memory
    - Key-value storage
    - Namespace support
    - TTL (time-to-live) support
    - In-memory store

### Task Management

11. **TodoWrite** - Write/update todo items
    - CRUD operations for todos
    - Status tracking (pending, in_progress, completed)
    - Namespace organization
    - UUID generation

12. **TodoRead** - Read todo items
    - Status filtering
    - Namespace support
    - Returns all or filtered todos

13. **TodoPause** - Pause execution
    - Return control to user
    - Optional pause message
    - Preserves todo state

## Usage

### In Agent Configuration

```yaml
agents:
  my_agent:
    model: gpt-4
    tools:
      - FindFiles
      - ReadFile
      - WriteFile
      - Shell
      - WebFetch
      - GoogleSearch
      - SaveMemory
      - TodoWrite
      - TodoRead
      - TodoPause
      - SearchText
      - ReadFolder
      - ReadManyFiles
```

### Tool Execution

Tools are automatically executed when:

1. **LLM calls a tool** - The LLM decides to use a tool based on the task
2. **Tool executor routes the call** - `ToolExecutor.execute_async()` is called
3. **Tool handler runs** - The tool's Python function executes
4. **Result is returned** - Tool result is provided to the LLM

### Unified Interface

All executors use the same interface:

```python
# Get tool by name
tool = tool_executor.get_tool("ReadFile")

# Execute tool
result = await tool_executor.execute_async(
    "ReadFile",
    {"file_path": "example.txt"}
)

# Result format
{
    "content": "file contents...",
    "path": "/absolute/path/to/example.txt",
    "size": 1234,
    "lines": 42
}
```

## Benefits of Unified System

1. **Consistency** - Same tools work identically across all execution paths
2. **Maintainability** - Single source of truth for tool implementations
3. **Extensibility** - Easy to add new tools
4. **Testing** - Tools can be tested in isolation
5. **OpenAI Compatibility** - OpenAI API server has full tool support

## Adding New Tools

To add a new tool:

1. Create the tool function in `tools/comprehensive.py`:

```python
def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """Tool description."""
    try:
        # Implementation
        return {"result": "success", "data": {...}}
    except Exception as e:
        return {"error": str(e)}
```

2. Add the tool definition:

```python
Tool(
    definition=ToolDefinition(
        name="MyNewTool",
        description="Description of what the tool does",
        parameters=[
            ToolParameter(
                name="param1",
                type=ParameterType.STRING,
                description="Parameter description",
                required=True,
            ),
            ToolParameter(
                name="param2",
                type=ParameterType.INTEGER,
                description="Parameter description",
                required=False,
                default=10,
            ),
        ],
        category="category_name",
        tags=["tag1", "tag2"],
    ),
    handler=my_new_tool,
)
```

3. Add to `get_comprehensive_tools()` list

4. The tool is now available in all executors!

## Tool Categories

- **filesystem** - File and directory operations
- **search** - Text and file search operations
- **system** - Shell and system operations
- **web** - HTTP and web operations
- **memory** - Memory and state management
- **task** - Task and todo management

## Error Handling

All tools follow a consistent error pattern:

**Success:**
```python
{
    "result": "...",
    "additional_data": "..."
}
```

**Error:**
```python
{
    "error": "Error message",
    "context": "..."
}
```

This ensures tools can be safely used by both LLMs and programmatic code.

## Testing

Test tools using the ToolExecutor:

```python
from weave.tools.executor import ToolExecutor

# Initialize
executor = ToolExecutor()

# List available tools
tools = executor.list_tools()

# Execute a tool
result = await executor.execute_async(
    "ReadFile",
    {"file_path": "test.txt"}
)
```

## Future Enhancements

- **Tool chaining** - Automatically chain tool outputs as inputs
- **Tool validation** - Enhanced parameter validation
- **Tool permissions** - Fine-grained access control
- **Tool metrics** - Usage tracking and performance monitoring
- **Tool streaming** - Support for streaming tool outputs
