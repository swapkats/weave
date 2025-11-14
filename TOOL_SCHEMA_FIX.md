# Tool Schema Format Fix

## Issue

The tool schema format was causing 400 BadRequestError when using tools with OpenAI-compatible APIs (like Gemini). The error message indicated:

```
Invalid JSON payload received. Unknown name "name" at 'tools[0]': Cannot find field.
Invalid JSON payload received. Unknown name "description" at 'tools[0]': Cannot find field.
Invalid JSON payload received. Unknown name "parameters" at 'tools[0]': Cannot find field.
```

This happened because the tool schemas were being sent in the wrong format.

## Root Cause

OpenAI and Anthropic have different tool schema formats:

**OpenAI/Gemini Format:**
```json
{
  "type": "function",
  "function": {
    "name": "ReadFile",
    "description": "Read file contents",
    "parameters": {
      "type": "object",
      "properties": {...},
      "required": [...]
    }
  }
}
```

**Anthropic Format:**
```json
{
  "name": "ReadFile",
  "description": "Read file contents",
  "input_schema": {
    "type": "object",
    "properties": {...},
    "required": [...]
  }
}
```

The original `to_json_schema()` method was returning a format that didn't match either API correctly.

## Solution

### 1. Updated `ToolDefinition.to_json_schema()` Method

Added a `format` parameter to support both formats:

```python
def to_json_schema(self, format: str = "openai") -> Dict[str, Any]:
    """Convert tool definition to LLM provider format.

    Args:
        format: "openai" for OpenAI/Gemini format, "anthropic" for Anthropic format
    """
    # ... build parameters schema ...

    if format == "anthropic":
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": parameters_schema,
        }
    else:
        # OpenAI/Gemini format (default)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters_schema,
            },
        }
```

### 2. Updated LLM Executor

The Anthropic API call now automatically converts OpenAI format to Anthropic format:

```python
# Convert from OpenAI format to Anthropic format
if "function" in tool:
    func = tool["function"]
    anthropic_tools.append({
        "name": func["name"],
        "description": func["description"],
        "input_schema": func["parameters"],
    })
```

### 3. Updated Executors

Both the main executor and OpenAI server now explicitly request OpenAI format:

```python
schema = tool.definition.to_json_schema("openai")
```

## Result

- ✅ Tools now work correctly with OpenAI API
- ✅ Tools now work correctly with Gemini API (OpenAI-compatible)
- ✅ Tools now work correctly with Anthropic API
- ✅ Automatic format conversion ensures compatibility
- ✅ No breaking changes to existing code

## Testing

To test the fix:

1. Start the OpenAI server with tools enabled
2. Make a request that triggers tool usage
3. Verify tools execute without 400 errors

Example agent config:
```yaml
agents:
  test_agent:
    model: gemini-pro
    tools:
      - ReadFile
      - WriteFile
      - Shell
```

## Files Modified

- `src/weave/tools/models.py` - Added format parameter to `to_json_schema()`
- `src/weave/runtime/llm_executor.py` - Added format conversion for Anthropic
- `src/weave/runtime/executor.py` - Explicitly use OpenAI format
- `src/weave/api/openai_server.py` - Explicitly use OpenAI format

## Additional Note

There was also a warning about "Save Memory" tool not found. Users should ensure their agent configurations use the correct tool name: `SaveMemory` (no space), not "Save Memory".
