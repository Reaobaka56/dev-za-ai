"""Tool definitions for the agent to interact with the system."""
import os
import subprocess
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import difflib


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None


class FileTools:
    """File system operations for the agent."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()

    def read_file(self, file_path: str, offset: int = 0, limit: int = 100) -> ToolResult:
        """Read contents of a file."""
        try:
            path = self._resolve_path(file_path)
            if not path.exists():
                return ToolResult(False, "", f"File not found: {file_path}")

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                selected = lines[offset:offset + limit]
                content = "".join(selected)
                total_lines = len(lines)

            return ToolResult(
                True, 
                f"--- {file_path} (lines {offset+1}-{min(offset+limit, total_lines)} of {total_lines}) ---\n{content}"
            )
        except Exception as e:
            return ToolResult(False, "", str(e))

    def write_file(self, file_path: str, content: str) -> ToolResult:
        """Write content to a file."""
        try:
            path = self._resolve_path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(True, f"Successfully wrote {len(content)} chars to {file_path}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def apply_patch(self, file_path: str, original: str, replacement: str) -> ToolResult:
        """Apply a patch by replacing original text with replacement."""
        try:
            path = self._resolve_path(file_path)
            if not path.exists():
                return ToolResult(False, "", f"File not found: {file_path}")

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if original not in content:
                return ToolResult(False, "", "Original text not found in file")

            new_content = content.replace(original, replacement, 1)

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Generate diff
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=file_path,
                tofile=file_path,
                lineterm=""
            )

            return ToolResult(True, f"Patch applied successfully.\n\nDiff:\n{''.join(diff)}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def list_files(self, directory: str = ".", pattern: str = "*") -> ToolResult:
        """List files in a directory."""
        try:
            path = self._resolve_path(directory)
            if not path.is_dir():
                return ToolResult(False, "", f"Not a directory: {directory}")

            files = []
            for item in path.rglob(pattern) if "**" in pattern else path.glob(pattern):
                if item.is_file():
                    rel = item.relative_to(self.root_dir)
                    files.append(str(rel))

            return ToolResult(True, "\n".join(sorted(files)))
        except Exception as e:
            return ToolResult(False, "", str(e))

    def search_code(self, query: str, directory: str = ".") -> ToolResult:
        """Search for text in code files."""
        try:
            path = self._resolve_path(directory)
            results = []

            code_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cpp", ".c", ".h"}

            for item in path.rglob("*"):
                if item.is_file() and item.suffix in code_exts:
                    try:
                        with open(item, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                lines = content.split("\n")
                                for i, line in enumerate(lines):
                                    if query.lower() in line.lower():
                                        rel = item.relative_to(self.root_dir)
                                        results.append(f"{rel}:{i+1}: {line.strip()}")
                                        if len(results) >= 20:
                                            break
                                if len(results) >= 20:
                                    break
                    except:
                        continue

            return ToolResult(True, "\n".join(results) if results else "No matches found.")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve path relative to root directory."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.root_dir / path
        return path.resolve()


class TerminalTools:
    """Terminal/command execution tools."""

    def __init__(self, cwd: str = "."):
        self.cwd = Path(cwd).resolve()

    def run_command(self, command: str, timeout: int = 30) -> ToolResult:
        """Run a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr

            return ToolResult(
                result.returncode == 0,
                output,
                None if result.returncode == 0 else f"Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def run_tests(self, test_path: str = ".") -> ToolResult:
        """Run pytest on the given path."""
        return self.run_command(f"python -m pytest {test_path} -v")

    def run_linter(self, file_path: str = ".") -> ToolResult:
        """Run ruff linter."""
        return self.run_command(f"ruff check {file_path}")


class GitTools:
    """Git operations for the agent."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.terminal = TerminalTools(str(self.repo_path))

    def status(self) -> ToolResult:
        return self.terminal.run_command("git status")

    def diff(self) -> ToolResult:
        return self.terminal.run_command("git diff")

    def commit(self, message: str) -> ToolResult:
        return self.terminal.run_command(f'git commit -am "{message}"')

    def create_branch(self, branch_name: str) -> ToolResult:
        return self.terminal.run_command(f"git checkout -b {branch_name}")

    def log(self, n: int = 5) -> ToolResult:
        return self.terminal.run_command(f'git log --oneline -{n}')

    def get_current_branch(self) -> str:
        result = self.terminal.run_command("git branch --show-current")
        return result.output.strip() if result.success else "main"


# Tool schemas for LLM function calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Use offset and limit to read specific sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "offset": {"type": "integer", "description": "Line offset to start reading from", "default": 0},
                    "limit": {"type": "integer", "description": "Number of lines to read", "default": 100}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": "Apply a patch by replacing original text with new text. Original must match exactly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "original": {"type": "string", "description": "Original text to replace"},
                    "replacement": {"type": "string", "description": "Replacement text"}
                },
                "required": ["file_path", "original", "replacement"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory matching a pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to list", "default": "."},
                    "pattern": {"type": "string", "description": "Glob pattern", "default": "*"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for text across all code files in the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text to search for"},
                    "directory": {"type": "string", "description": "Directory to search in", "default": "."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command in the project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the test suite using pytest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "Path to tests", "default": "."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Check git status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show git diff of current changes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
