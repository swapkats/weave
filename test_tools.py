#!/usr/bin/env python3
"""Test script for comprehensive tools."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from weave.tools.executor import ToolExecutor


async def test_tools():
    """Test all comprehensive tools."""
    print("=" * 60)
    print("Testing Weave Comprehensive Tools")
    print("=" * 60)

    # Initialize tool executor
    executor = ToolExecutor()

    # List all available tools
    tools = executor.list_tools()
    print(f"\n✓ Loaded {len(tools)} tools")

    # Expected comprehensive tools
    expected_tools = [
        "FindFiles",
        "ReadFile",
        "ReadFolder",
        "ReadManyFiles",
        "WriteFile",
        "SearchText",
        "Shell",
        "WebFetch",
        "GoogleSearch",
        "SaveMemory",
        "TodoWrite",
        "TodoRead",
        "TodoPause",
    ]

    print("\nChecking comprehensive tools:")
    for tool_name in expected_tools:
        tool = executor.get_tool(tool_name)
        if tool:
            print(f"  ✓ {tool_name:20} - {tool.definition.description}")
        else:
            print(f"  ✗ {tool_name:20} - NOT FOUND")

    # Test some basic tools
    print("\n" + "=" * 60)
    print("Running Basic Tool Tests")
    print("=" * 60)

    # Test 1: WriteFile
    print("\n[Test 1] WriteFile")
    result = await executor.execute_async(
        "WriteFile",
        {
            "file_path": "/tmp/test_weave.txt",
            "content": "Hello from Weave unified tools!\n"
        }
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ File written: {result.get('path')}")
        print(f"    Size: {result.get('size')} bytes")

    # Test 2: ReadFile
    print("\n[Test 2] ReadFile")
    result = await executor.execute_async(
        "ReadFile",
        {"file_path": "/tmp/test_weave.txt"}
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ File read: {result.get('path')}")
        print(f"    Content: {result.get('content', '').strip()}")
        print(f"    Lines: {result.get('lines')}")

    # Test 3: FindFiles
    print("\n[Test 3] FindFiles")
    result = await executor.execute_async(
        "FindFiles",
        {
            "pattern": "*.py",
            "path": ".",
            "max_results": 5
        }
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Found {result.get('count')} files")
        for f in result.get('files', [])[:3]:
            print(f"    - {f}")

    # Test 4: Shell
    print("\n[Test 4] Shell")
    result = await executor.execute_async(
        "Shell",
        {"command": "echo 'Hello from shell'"}
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Command executed")
        print(f"    Exit code: {result.get('exit_code')}")
        print(f"    Output: {result.get('stdout', '').strip()}")

    # Test 5: SaveMemory & ReadMemory
    print("\n[Test 5] SaveMemory")
    result = await executor.execute_async(
        "SaveMemory",
        {
            "key": "test_key",
            "value": "test_value",
            "namespace": "test"
        }
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Memory saved: {result.get('full_key')}")

    # Test 6: TodoWrite
    print("\n[Test 6] TodoWrite")
    result = await executor.execute_async(
        "TodoWrite",
        {
            "todos": [
                {"content": "Test task 1", "status": "pending"},
                {"content": "Test task 2", "status": "in_progress"},
                {"content": "Test task 3", "status": "completed"}
            ],
            "namespace": "test"
        }
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Todos written: {result.get('todo_count')} items")

    # Test 7: TodoRead
    print("\n[Test 7] TodoRead")
    result = await executor.execute_async(
        "TodoRead",
        {"namespace": "test", "status_filter": "pending"}
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Todos read: {result.get('todo_count')} items")
        for todo in result.get('todos', []):
            print(f"    - [{todo.get('status')}] {todo.get('content')}")

    # Test 8: ReadFolder
    print("\n[Test 8] ReadFolder")
    result = await executor.execute_async(
        "ReadFolder",
        {"directory": ".", "pattern": "*.md"}
    )
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Directory read: {result.get('file_count')} files")
        for f in result.get('files', [])[:3]:
            print(f"    - {f}")

    print("\n" + "=" * 60)
    print("All Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tools())
