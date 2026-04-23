"""Core agent orchestrator with reasoning loop and tool use."""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .llm import LLMClient, Message, MockLLMClient
from .tools import (
    FileTools, TerminalTools, GitTools, 
    ToolResult, TOOL_SCHEMAS
)
from .memory import AgentMemory, SimpleMemory
from .code_parser import CodeParser


class AgentMode(Enum):
    FIX = "fix"
    EXPLAIN = "explain"
    REFACTOR = "refactor"
    ASK = "ask"
    INDEX = "index"
    CHAT = "chat"


@dataclass
class AgentState:
    """Current state of the agent session."""
    mode: AgentMode
    target_file: Optional[str] = None
    description: str = ""
    messages: List[Message] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 10


class AgentOrchestrator:
    """Main agent that orchestrates LLM reasoning + tool use."""

    SYSTEM_PROMPT = """You are an expert AI software engineer. You help developers understand, fix, and improve code.

You have access to tools to read files, search code, run commands, and apply patches. Use them proactively.

Rules:
1. Always read relevant files before making changes
2. Search the codebase to understand context
3. Apply changes using apply_patch (not write_file for edits)
4. Run tests after making changes
5. Explain your reasoning clearly
6. If you need more info, ask or search

When fixing bugs:
- Identify the root cause first
- Make minimal, targeted fixes
- Verify with tests

When explaining code:
- Start with high-level purpose
- Break down key functions/classes
- Mention important patterns or dependencies

When refactoring:
- Preserve behavior
- Improve readability and maintainability
- Follow language best practices
"""

    def __init__(self, 
                 root_dir: str = ".",
                 llm_client: Optional[LLMClient] = None,
                 memory: Optional[AgentMemory] = None):
        self.root_dir = Path(root_dir).resolve()
        self.llm = llm_client or LLMClient()
        self.memory = memory or AgentMemory(llm_client=self.llm)
        self.file_tools = FileTools(str(self.root_dir))
        self.terminal = TerminalTools(str(self.root_dir))
        self.git = GitTools(str(self.root_dir))
        self.parser = CodeParser()
        self._tool_map = self._build_tool_map()

    def _build_tool_map(self) -> Dict[str, Any]:
        """Map tool names to actual functions."""
        return {
            "read_file": self.file_tools.read_file,
            "write_file": self.file_tools.write_file,
            "apply_patch": self.file_tools.apply_patch,
            "list_files": self.file_tools.list_files,
            "search_code": self.file_tools.search_code,
            "run_command": self.terminal.run_command,
            "run_tests": self.terminal.run_tests,
            "git_status": self.git.status,
            "git_diff": self.git.diff,
        }

    async def run(self, 
                  mode: AgentMode, 
                  target: Optional[str] = None,
                  description: str = "",
                  stream: bool = False) -> AsyncGenerator[str, None]:
        """Main agent loop."""

        state = AgentState(
            mode=mode,
            target_file=target,
            description=description,
            messages=[
                Message(role="system", content=self.SYSTEM_PROMPT)
            ],
            max_iterations=10
        )

        # Build initial user message based on mode
        user_msg = self._build_initial_message(state)
        state.messages.append(Message(role="user", content=user_msg))

        yield f"🤖 Starting {mode.value} mode...\n"
        yield f"📁 Working directory: {self.root_dir}\n"
        yield "─" * 50 + "\n"

        # Main reasoning loop
        while state.iteration < state.max_iterations:
            state.iteration += 1
            yield f"\n🔄 Step {state.iteration}/{state.max_iterations}\n"

            # Get LLM response with tool schemas
            response = await self.llm.chat(
                messages=state.messages,
                tools=TOOL_SCHEMAS,
                temperature=0.1
            )

            state.messages.append(response)

            # Check if LLM wants to use tools
            if response.tool_calls:
                yield f"🔧 Using tools...\n"

                for tool_call in response.tool_calls:
                    result = await self._execute_tool(tool_call)
                    state.tool_results.append({
                        "tool": tool_call["function"]["name"],
                        "result": result
                    })

                    # Add tool result to messages
                    state.messages.append(Message(
                        role="tool",
                        content=result.output if result.success else f"Error: {result.error}",
                        tool_call_id=tool_call["id"],
                        name=tool_call["function"]["name"]
                    ))

                    status = "✅" if result.success else "❌"
                    yield f"{status} {tool_call['function']['name']}: {result.output[:200]}...\n"

                # Continue loop for more reasoning
                continue

            else:
                # LLM provided final answer
                yield f"\n✨ Final Answer:\n"
                yield response.content
                yield "\n"

                # Auto-commit if we made changes
                if state.mode in (AgentMode.FIX, AgentMode.REFACTOR):
                    commit_msg = f"AI: {state.mode.value} {state.target_file or ''} - {state.description[:50]}"
                    git_result = self.git.commit(commit_msg)
                    if git_result.success:
                        yield f"\n📝 Auto-committed: {commit_msg}\n"

                break

        if state.iteration >= state.max_iterations:
            yield "\n⚠️ Reached maximum iterations. Stopping.\n"

    def _build_initial_message(self, state: AgentState) -> str:
        """Build the initial user message based on agent mode."""

        if state.mode == AgentMode.FIX:
            return f"""Fix the bug in {state.target_file}.

Description: {state.description}

Steps:
1. Read the file to understand the issue
2. Search for related code if needed
3. Apply a minimal fix
4. Run tests to verify
5. Explain what was wrong and how you fixed it"""

        elif state.mode == AgentMode.EXPLAIN:
            return f"""Explain the code in {state.target_file}.

Provide:
1. High-level purpose of the file
2. Key functions/classes and what they do
3. Important dependencies and patterns
4. Any notable design decisions"""

        elif state.mode == AgentMode.REFACTOR:
            return f"""Refactor {state.target_file} for better quality.

Description: {state.description}

Goals:
1. Improve readability and maintainability
2. Follow best practices for the language
3. Preserve all existing behavior
4. Run tests to ensure nothing broke
5. Explain the changes made"""

        elif state.mode == AgentMode.ASK:
            return f"""Answer this question about the codebase: {state.description}

Use search_code and read_file to find relevant information.
Provide a comprehensive answer with code references."""

        elif state.mode == AgentMode.INDEX:
            return "Index the project for better code understanding."

        elif state.mode == AgentMode.CHAT:
            return state.description

        return state.description

    async def _execute_tool(self, tool_call: Dict) -> ToolResult:
        """Execute a tool call from the LLM."""
        func_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        if func_name not in self._tool_map:
            return ToolResult(False, "", f"Unknown tool: {func_name}")

        func = self._tool_map[func_name]

        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(func):
                return await func(**arguments)
            else:
                return func(**arguments)
        except Exception as e:
            return ToolResult(False, "", str(e))

    async def index_project(self, directory: str = ".") -> Dict[str, Any]:
        """Index the project into memory."""
        result = await self.memory.index_project(directory)
        return result

    async def search_memory(self, query: str, n: int = 5) -> List[Dict]:
        """Search the memory for relevant code."""
        return await self.memory.search(query, n)

    def get_memory_stats(self) -> Dict[str, Any]:
        return self.memory.get_stats()


class SimpleAgent:
    """Simplified agent for quick operations without full orchestration."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.file_tools = FileTools(str(self.root_dir))
        self.parser = CodeParser()

    def explain_file(self, file_path: str) -> str:
        """Quick file explanation without LLM."""
        summary = self.parser.get_file_summary(file_path)

        lines = [
            f"📄 {summary['file']}",
            f"🌐 Language: {summary['language'] or 'unknown'}",
            f"📏 Lines: {summary['total_lines']}",
            "",
        ]

        if summary['classes']:
            lines.append("🏗️  Classes:")
            for cls in summary['classes']:
                lines.append(f"   • {cls}")
            lines.append("")

        if summary['functions']:
            lines.append("⚙️  Functions:")
            for func in summary['functions']:
                lines.append(f"   • {func}")
            lines.append("")

        if summary['imports']:
            lines.append("📦 Imports:")
            for imp in summary['imports'][:10]:
                lines.append(f"   {imp}")
            if len(summary['imports']) > 10:
                lines.append(f"   ... and {len(summary['imports']) - 10} more")

        return "\n".join(lines)
