"""Comprehensive tool set for Weave agents.

This module provides a complete set of tools for file operations, web access,
memory management, and task tracking.
"""

import os
import json
import glob as glob_module
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path

from weave.tools.models import Tool, ToolDefinition, ToolParameter, ParameterType


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def find_files(pattern: str, path: str = ".", recursive: bool = True, max_results: int = 100) -> Dict[str, Any]:
    """Find files matching a pattern.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "**/*.ts")
        path: Starting directory path
        recursive: Whether to search recursively
        max_results: Maximum number of results to return

    Returns:
        Dict containing list of matching files
    """
    try:
        search_path = Path(path).expanduser().resolve()

        if not search_path.exists():
            return {"error": f"Path not found: {path}"}

        if not search_path.is_dir():
            return {"error": f"Not a directory: {path}"}

        # Use glob to find files
        if recursive:
            matches = list(search_path.rglob(pattern))
        else:
            matches = list(search_path.glob(pattern))

        # Filter to only files
        files = [str(p.relative_to(search_path)) for p in matches if p.is_file()][:max_results]

        return {
            "files": files,
            "count": len(files),
            "pattern": pattern,
            "search_path": str(search_path),
            "truncated": len(matches) > max_results
        }
    except Exception as e:
        return {"error": str(e), "pattern": pattern, "path": path}


def read_file(file_path: str, encoding: str = "utf-8", max_size: int = 1000000) -> Dict[str, Any]:
    """Read file contents.

    Args:
        file_path: Path to file to read
        encoding: File encoding
        max_size: Maximum file size to read (in bytes)

    Returns:
        Dict containing file contents and metadata
    """
    try:
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        if not path.is_file():
            return {"error": f"Not a file: {file_path}"}

        # Check file size
        size = path.stat().st_size
        if size > max_size:
            return {
                "error": f"File too large: {size} bytes (max: {max_size})",
                "path": str(path),
                "size": size
            }

        content = path.read_text(encoding=encoding)

        return {
            "content": content,
            "path": str(path),
            "size": size,
            "lines": len(content.splitlines()),
            "encoding": encoding
        }
    except Exception as e:
        return {"error": str(e), "path": file_path}


def read_folder(directory: str, pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
    """List contents of a directory.

    Args:
        directory: Directory path to read
        pattern: Pattern to filter results
        recursive: Whether to list recursively

    Returns:
        Dict containing directory contents
    """
    try:
        path = Path(directory).expanduser().resolve()

        if not path.exists():
            return {"error": f"Directory not found: {directory}"}

        if not path.is_dir():
            return {"error": f"Not a directory: {directory}"}

        if recursive:
            all_paths = list(path.rglob(pattern))
            files = [str(p.relative_to(path)) for p in all_paths if p.is_file()]
            dirs = [str(p.relative_to(path)) for p in all_paths if p.is_dir()]
        else:
            all_paths = list(path.glob(pattern))
            files = [p.name for p in all_paths if p.is_file()]
            dirs = [p.name for p in all_paths if p.is_dir()]

        return {
            "directory": str(path),
            "files": sorted(files),
            "directories": sorted(dirs),
            "file_count": len(files),
            "directory_count": len(dirs),
            "pattern": pattern,
            "recursive": recursive
        }
    except Exception as e:
        return {"error": str(e), "directory": directory}


def read_many_files(file_paths: List[str], encoding: str = "utf-8", max_size_per_file: int = 500000) -> Dict[str, Any]:
    """Read multiple files at once.

    Args:
        file_paths: List of file paths to read
        encoding: File encoding
        max_size_per_file: Maximum size per file (in bytes)

    Returns:
        Dict containing contents of all files
    """
    try:
        results = []
        total_size = 0
        errors = []

        for file_path in file_paths:
            result = read_file(file_path, encoding=encoding, max_size=max_size_per_file)

            if "error" in result:
                errors.append({"path": file_path, "error": result["error"]})
            else:
                results.append({
                    "path": result["path"],
                    "content": result["content"],
                    "size": result["size"],
                    "lines": result["lines"]
                })
                total_size += result["size"]

        return {
            "files": results,
            "file_count": len(results),
            "total_size": total_size,
            "errors": errors,
            "error_count": len(errors)
        }
    except Exception as e:
        return {"error": str(e), "file_paths": file_paths}


def write_file(file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True, append: bool = False) -> Dict[str, Any]:
    """Write content to a file.

    Args:
        file_path: Path to file to write
        content: Content to write
        encoding: File encoding
        create_dirs: Create parent directories if they don't exist
        append: Append to file instead of overwriting

    Returns:
        Dict containing write operation result
    """
    try:
        path = Path(file_path).expanduser().resolve()

        # Create parent directories if needed
        if create_dirs and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        if append and path.exists():
            existing_content = path.read_text(encoding=encoding)
            content = existing_content + content

        path.write_text(content, encoding=encoding)

        return {
            "success": True,
            "path": str(path),
            "size": len(content),
            "lines": len(content.splitlines()),
            "mode": "append" if append else "write"
        }
    except Exception as e:
        return {"error": str(e), "path": file_path}


def search_text(pattern: str, path: str = ".", file_pattern: str = "*", recursive: bool = True, max_results: int = 100, context_lines: int = 0) -> Dict[str, Any]:
    """Search for text pattern in files.

    Args:
        pattern: Text pattern to search for (supports regex)
        path: Directory to search in
        file_pattern: Pattern for files to search (e.g., "*.py")
        recursive: Whether to search recursively
        max_results: Maximum number of results
        context_lines: Number of context lines to include

    Returns:
        Dict containing search results
    """
    try:
        import re

        search_path = Path(path).expanduser().resolve()

        if not search_path.exists():
            return {"error": f"Path not found: {path}"}

        if not search_path.is_dir():
            return {"error": f"Not a directory: {path}"}

        # Compile regex pattern
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return {"error": f"Invalid regex pattern: {e}"}

        # Find files to search
        if recursive:
            files = list(search_path.rglob(file_pattern))
        else:
            files = list(search_path.glob(file_pattern))

        results = []
        files_searched = 0

        for file_path in files:
            if not file_path.is_file():
                continue

            files_searched += 1

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.splitlines()

                for i, line in enumerate(lines):
                    if regex.search(line):
                        match_result = {
                            "file": str(file_path.relative_to(search_path)),
                            "line_number": i + 1,
                            "line": line.strip(),
                            "context": []
                        }

                        # Add context lines
                        if context_lines > 0:
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            match_result["context"] = [
                                {"line_number": j + 1, "line": lines[j].strip()}
                                for j in range(start, end)
                            ]

                        results.append(match_result)

                        if len(results) >= max_results:
                            break
            except Exception:
                # Skip files that can't be read
                continue

            if len(results) >= max_results:
                break

        return {
            "matches": results,
            "match_count": len(results),
            "files_searched": files_searched,
            "pattern": pattern,
            "truncated": len(results) >= max_results
        }
    except Exception as e:
        return {"error": str(e), "pattern": pattern, "path": path}


# ============================================================================
# SHELL / SYSTEM OPERATIONS
# ============================================================================

def shell(command: str, timeout: int = 30, working_dir: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Execute a shell command.

    Args:
        command: Command to execute
        timeout: Timeout in seconds
        working_dir: Working directory for command
        env: Environment variables to set

    Returns:
        Dict containing command output and status
    """
    try:
        # Set working directory
        cwd = Path(working_dir).expanduser().resolve() if working_dir else None

        # Validate working directory
        if cwd and not cwd.exists():
            return {"error": f"Working directory not found: {working_dir}"}

        if cwd and not cwd.is_dir():
            return {"error": f"Not a directory: {working_dir}"}

        # Prepare environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=exec_env
        )

        return {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "working_dir": str(cwd) if cwd else os.getcwd()
        }
    except subprocess.TimeoutExpired:
        return {
            "error": f"Command timed out after {timeout} seconds",
            "command": command,
            "timeout": timeout
        }
    except Exception as e:
        return {"error": str(e), "command": command}


# ============================================================================
# WEB OPERATIONS
# ============================================================================

def web_fetch(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """Fetch content from a URL.

    Args:
        url: URL to fetch
        method: HTTP method (GET, POST, etc.)
        headers: HTTP headers
        body: Request body
        timeout: Request timeout in seconds

    Returns:
        Dict containing response data
    """
    try:
        import requests

        method = method.upper()
        headers = headers or {}

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=body, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, headers=headers, data=body, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, data=body, timeout=timeout)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        return {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "success": 200 <= response.status_code < 300
        }
    except ImportError:
        return {"error": "requests library required. Install: pip install requests"}
    except Exception as e:
        return {"error": str(e), "url": url, "method": method}


def google_search(query: str, num_results: int = 10, language: str = "en") -> Dict[str, Any]:
    """Search Google for a query.

    Args:
        query: Search query
        num_results: Number of results to return
        language: Language code

    Returns:
        Dict containing search results
    """
    try:
        # Try using googlesearch-python library
        try:
            from googlesearch import search as google_search_lib

            results = []
            for url in google_search_lib(query, num_results=num_results, lang=language):
                results.append({"url": url})

            return {
                "query": query,
                "results": results,
                "result_count": len(results),
                "language": language
            }
        except ImportError:
            # Fallback: Use DuckDuckGo or return instructions
            return {
                "error": "googlesearch-python not installed",
                "message": "Install with: pip install googlesearch-python",
                "alternative": "You can also use DuckDuckGo search or other search APIs",
                "query": query
            }
    except Exception as e:
        return {"error": str(e), "query": query}


# ============================================================================
# MEMORY OPERATIONS
# ============================================================================

_MEMORY_STORE: Dict[str, Any] = {}

def save_memory(key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> Dict[str, Any]:
    """Save a value to memory.

    Args:
        key: Memory key
        value: Value to store
        namespace: Memory namespace
        ttl: Time to live in seconds (optional)

    Returns:
        Dict containing save operation result
    """
    try:
        import time

        full_key = f"{namespace}:{key}"

        memory_entry = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl
        }

        _MEMORY_STORE[full_key] = memory_entry

        return {
            "success": True,
            "key": key,
            "namespace": namespace,
            "full_key": full_key,
            "ttl": ttl
        }
    except Exception as e:
        return {"error": str(e), "key": key, "namespace": namespace}


def read_memory(key: str, namespace: str = "default", default: Any = None) -> Dict[str, Any]:
    """Read a value from memory.

    Args:
        key: Memory key
        namespace: Memory namespace
        default: Default value if not found

    Returns:
        Dict containing memory value
    """
    try:
        import time

        full_key = f"{namespace}:{key}"

        if full_key not in _MEMORY_STORE:
            return {
                "found": False,
                "key": key,
                "namespace": namespace,
                "value": default
            }

        entry = _MEMORY_STORE[full_key]

        # Check TTL
        if entry["ttl"] is not None:
            age = time.time() - entry["timestamp"]
            if age > entry["ttl"]:
                del _MEMORY_STORE[full_key]
                return {
                    "found": False,
                    "key": key,
                    "namespace": namespace,
                    "value": default,
                    "expired": True
                }

        return {
            "found": True,
            "key": key,
            "namespace": namespace,
            "value": entry["value"],
            "timestamp": entry["timestamp"]
        }
    except Exception as e:
        return {"error": str(e), "key": key, "namespace": namespace}


# ============================================================================
# TODO OPERATIONS
# ============================================================================

_TODO_STORE: Dict[str, List[Dict[str, Any]]] = {}

def todo_write(todos: List[Dict[str, Any]], namespace: str = "default") -> Dict[str, Any]:
    """Write todo items.

    Args:
        todos: List of todo items with 'content', 'status', and optional 'id'
        namespace: Todo namespace

    Returns:
        Dict containing write operation result
    """
    try:
        import uuid

        # Ensure each todo has an ID
        for todo in todos:
            if "id" not in todo:
                todo["id"] = str(uuid.uuid4())
            if "status" not in todo:
                todo["status"] = "pending"

        _TODO_STORE[namespace] = todos

        return {
            "success": True,
            "namespace": namespace,
            "todo_count": len(todos),
            "todos": todos
        }
    except Exception as e:
        return {"error": str(e), "namespace": namespace}


def todo_read(namespace: str = "default", status_filter: Optional[str] = None) -> Dict[str, Any]:
    """Read todo items.

    Args:
        namespace: Todo namespace
        status_filter: Filter by status (pending, in_progress, completed)

    Returns:
        Dict containing todo items
    """
    try:
        todos = _TODO_STORE.get(namespace, [])

        if status_filter:
            todos = [t for t in todos if t.get("status") == status_filter]

        return {
            "success": True,
            "namespace": namespace,
            "todo_count": len(todos),
            "todos": todos,
            "status_filter": status_filter
        }
    except Exception as e:
        return {"error": str(e), "namespace": namespace}


def todo_pause(namespace: str = "default", message: Optional[str] = None) -> Dict[str, Any]:
    """Pause todo execution and return control.

    Args:
        namespace: Todo namespace
        message: Optional message about why pausing

    Returns:
        Dict containing pause operation result
    """
    try:
        import time

        return {
            "success": True,
            "action": "pause",
            "namespace": namespace,
            "message": message or "Pausing for user input",
            "timestamp": time.time(),
            "todos": _TODO_STORE.get(namespace, [])
        }
    except Exception as e:
        return {"error": str(e), "namespace": namespace}


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

def get_comprehensive_tools() -> List[Tool]:
    """Get all comprehensive tools.

    Returns:
        List of Tool instances
    """
    return [
        # File Operations
        Tool(
            definition=ToolDefinition(
                name="FindFiles",
                description="Find files matching a glob pattern in a directory",
                parameters=[
                    ToolParameter(
                        name="pattern",
                        type=ParameterType.STRING,
                        description="Glob pattern to match (e.g., '*.py', '**/*.ts')",
                        required=True,
                    ),
                    ToolParameter(
                        name="path",
                        type=ParameterType.STRING,
                        description="Starting directory path (default: current directory)",
                        required=False,
                        default=".",
                    ),
                    ToolParameter(
                        name="recursive",
                        type=ParameterType.BOOLEAN,
                        description="Whether to search recursively",
                        required=False,
                        default=True,
                    ),
                    ToolParameter(
                        name="max_results",
                        type=ParameterType.INTEGER,
                        description="Maximum number of results to return",
                        required=False,
                        default=100,
                    ),
                ],
                category="filesystem",
                tags=["file", "search", "find"],
            ),
            handler=find_files,
        ),
        Tool(
            definition=ToolDefinition(
                name="ReadFile",
                description="Read the contents of a file",
                parameters=[
                    ToolParameter(
                        name="file_path",
                        type=ParameterType.STRING,
                        description="Path to the file to read",
                        required=True,
                    ),
                    ToolParameter(
                        name="encoding",
                        type=ParameterType.STRING,
                        description="File encoding (default: utf-8)",
                        required=False,
                        default="utf-8",
                    ),
                    ToolParameter(
                        name="max_size",
                        type=ParameterType.INTEGER,
                        description="Maximum file size in bytes (default: 1MB)",
                        required=False,
                        default=1000000,
                    ),
                ],
                category="filesystem",
                tags=["file", "read", "io"],
            ),
            handler=read_file,
        ),
        Tool(
            definition=ToolDefinition(
                name="ReadFolder",
                description="List contents of a directory",
                parameters=[
                    ToolParameter(
                        name="directory",
                        type=ParameterType.STRING,
                        description="Directory path to read",
                        required=True,
                    ),
                    ToolParameter(
                        name="pattern",
                        type=ParameterType.STRING,
                        description="Pattern to filter results (default: all files)",
                        required=False,
                        default="*",
                    ),
                    ToolParameter(
                        name="recursive",
                        type=ParameterType.BOOLEAN,
                        description="Whether to list recursively",
                        required=False,
                        default=False,
                    ),
                ],
                category="filesystem",
                tags=["directory", "list", "folder"],
            ),
            handler=read_folder,
        ),
        Tool(
            definition=ToolDefinition(
                name="ReadManyFiles",
                description="Read multiple files at once",
                parameters=[
                    ToolParameter(
                        name="file_paths",
                        type=ParameterType.ARRAY,
                        description="List of file paths to read",
                        required=True,
                    ),
                    ToolParameter(
                        name="encoding",
                        type=ParameterType.STRING,
                        description="File encoding (default: utf-8)",
                        required=False,
                        default="utf-8",
                    ),
                    ToolParameter(
                        name="max_size_per_file",
                        type=ParameterType.INTEGER,
                        description="Maximum size per file in bytes (default: 500KB)",
                        required=False,
                        default=500000,
                    ),
                ],
                category="filesystem",
                tags=["file", "read", "batch"],
            ),
            handler=read_many_files,
        ),
        Tool(
            definition=ToolDefinition(
                name="WriteFile",
                description="Write content to a file",
                parameters=[
                    ToolParameter(
                        name="file_path",
                        type=ParameterType.STRING,
                        description="Path to the file to write",
                        required=True,
                    ),
                    ToolParameter(
                        name="content",
                        type=ParameterType.STRING,
                        description="Content to write to the file",
                        required=True,
                    ),
                    ToolParameter(
                        name="encoding",
                        type=ParameterType.STRING,
                        description="File encoding (default: utf-8)",
                        required=False,
                        default="utf-8",
                    ),
                    ToolParameter(
                        name="create_dirs",
                        type=ParameterType.BOOLEAN,
                        description="Create parent directories if they don't exist",
                        required=False,
                        default=True,
                    ),
                    ToolParameter(
                        name="append",
                        type=ParameterType.BOOLEAN,
                        description="Append to file instead of overwriting",
                        required=False,
                        default=False,
                    ),
                ],
                category="filesystem",
                tags=["file", "write", "io"],
            ),
            handler=write_file,
        ),
        Tool(
            definition=ToolDefinition(
                name="SearchText",
                description="Search for text pattern in files using regex",
                parameters=[
                    ToolParameter(
                        name="pattern",
                        type=ParameterType.STRING,
                        description="Text pattern to search for (supports regex)",
                        required=True,
                    ),
                    ToolParameter(
                        name="path",
                        type=ParameterType.STRING,
                        description="Directory to search in (default: current directory)",
                        required=False,
                        default=".",
                    ),
                    ToolParameter(
                        name="file_pattern",
                        type=ParameterType.STRING,
                        description="Pattern for files to search (e.g., '*.py')",
                        required=False,
                        default="*",
                    ),
                    ToolParameter(
                        name="recursive",
                        type=ParameterType.BOOLEAN,
                        description="Whether to search recursively",
                        required=False,
                        default=True,
                    ),
                    ToolParameter(
                        name="max_results",
                        type=ParameterType.INTEGER,
                        description="Maximum number of results",
                        required=False,
                        default=100,
                    ),
                    ToolParameter(
                        name="context_lines",
                        type=ParameterType.INTEGER,
                        description="Number of context lines to include",
                        required=False,
                        default=0,
                    ),
                ],
                category="search",
                tags=["text", "search", "grep", "regex"],
            ),
            handler=search_text,
        ),

        # Shell Operations
        Tool(
            definition=ToolDefinition(
                name="Shell",
                description="Execute a shell command and return output",
                parameters=[
                    ToolParameter(
                        name="command",
                        type=ParameterType.STRING,
                        description="Shell command to execute",
                        required=True,
                    ),
                    ToolParameter(
                        name="timeout",
                        type=ParameterType.INTEGER,
                        description="Timeout in seconds (default: 30)",
                        required=False,
                        default=30,
                    ),
                    ToolParameter(
                        name="working_dir",
                        type=ParameterType.STRING,
                        description="Working directory for command execution",
                        required=False,
                    ),
                    ToolParameter(
                        name="env",
                        type=ParameterType.OBJECT,
                        description="Environment variables to set",
                        required=False,
                    ),
                ],
                category="system",
                tags=["shell", "command", "execute", "bash"],
            ),
            handler=shell,
        ),

        # Web Operations
        Tool(
            definition=ToolDefinition(
                name="WebFetch",
                description="Fetch content from a URL",
                parameters=[
                    ToolParameter(
                        name="url",
                        type=ParameterType.STRING,
                        description="URL to fetch",
                        required=True,
                    ),
                    ToolParameter(
                        name="method",
                        type=ParameterType.STRING,
                        description="HTTP method (GET, POST, PUT, DELETE, PATCH)",
                        required=False,
                        default="GET",
                        enum=["GET", "POST", "PUT", "DELETE", "PATCH"],
                    ),
                    ToolParameter(
                        name="headers",
                        type=ParameterType.OBJECT,
                        description="HTTP headers",
                        required=False,
                    ),
                    ToolParameter(
                        name="body",
                        type=ParameterType.STRING,
                        description="Request body",
                        required=False,
                    ),
                    ToolParameter(
                        name="timeout",
                        type=ParameterType.INTEGER,
                        description="Request timeout in seconds",
                        required=False,
                        default=30,
                    ),
                ],
                category="web",
                tags=["http", "web", "fetch", "request"],
            ),
            handler=web_fetch,
        ),
        Tool(
            definition=ToolDefinition(
                name="GoogleSearch",
                description="Search Google for a query",
                parameters=[
                    ToolParameter(
                        name="query",
                        type=ParameterType.STRING,
                        description="Search query",
                        required=True,
                    ),
                    ToolParameter(
                        name="num_results",
                        type=ParameterType.INTEGER,
                        description="Number of results to return",
                        required=False,
                        default=10,
                    ),
                    ToolParameter(
                        name="language",
                        type=ParameterType.STRING,
                        description="Language code (e.g., 'en', 'es')",
                        required=False,
                        default="en",
                    ),
                ],
                category="web",
                tags=["search", "google", "web"],
            ),
            handler=google_search,
        ),

        # Memory Operations
        Tool(
            definition=ToolDefinition(
                name="SaveMemory",
                description="Save a value to memory for later retrieval",
                parameters=[
                    ToolParameter(
                        name="key",
                        type=ParameterType.STRING,
                        description="Memory key",
                        required=True,
                    ),
                    ToolParameter(
                        name="value",
                        type=ParameterType.STRING,
                        description="Value to store",
                        required=True,
                    ),
                    ToolParameter(
                        name="namespace",
                        type=ParameterType.STRING,
                        description="Memory namespace (default: 'default')",
                        required=False,
                        default="default",
                    ),
                    ToolParameter(
                        name="ttl",
                        type=ParameterType.INTEGER,
                        description="Time to live in seconds (optional)",
                        required=False,
                    ),
                ],
                category="memory",
                tags=["memory", "storage", "cache"],
            ),
            handler=save_memory,
        ),

        # Todo Operations
        Tool(
            definition=ToolDefinition(
                name="TodoWrite",
                description="Write or update todo items",
                parameters=[
                    ToolParameter(
                        name="todos",
                        type=ParameterType.ARRAY,
                        description="List of todo items with 'content', 'status', and optional 'id'",
                        required=True,
                    ),
                    ToolParameter(
                        name="namespace",
                        type=ParameterType.STRING,
                        description="Todo namespace (default: 'default')",
                        required=False,
                        default="default",
                    ),
                ],
                category="task",
                tags=["todo", "task", "tracking"],
            ),
            handler=todo_write,
        ),
        Tool(
            definition=ToolDefinition(
                name="TodoRead",
                description="Read todo items",
                parameters=[
                    ToolParameter(
                        name="namespace",
                        type=ParameterType.STRING,
                        description="Todo namespace (default: 'default')",
                        required=False,
                        default="default",
                    ),
                    ToolParameter(
                        name="status_filter",
                        type=ParameterType.STRING,
                        description="Filter by status (pending, in_progress, completed)",
                        required=False,
                        enum=["pending", "in_progress", "completed"],
                    ),
                ],
                category="task",
                tags=["todo", "task", "tracking"],
            ),
            handler=todo_read,
        ),
        Tool(
            definition=ToolDefinition(
                name="TodoPause",
                description="Pause todo execution and return control to user",
                parameters=[
                    ToolParameter(
                        name="namespace",
                        type=ParameterType.STRING,
                        description="Todo namespace (default: 'default')",
                        required=False,
                        default="default",
                    ),
                    ToolParameter(
                        name="message",
                        type=ParameterType.STRING,
                        description="Optional message about why pausing",
                        required=False,
                    ),
                ],
                category="task",
                tags=["todo", "task", "pause", "control"],
            ),
            handler=todo_pause,
        ),
    ]
