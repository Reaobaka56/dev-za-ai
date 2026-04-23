"""Tests for agent core."""
import pytest
from src.agent.core import SimpleAgent, AgentMode
from src.agent.llm import MockLLMClient


class TestSimpleAgent:
    def test_explain_file(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def add(a, b):\n"
            "    return a + b\n\n"
            "class Calculator:\n"
            "    def multiply(self, a, b):\n"
            "        return a * b\n"
        )

        agent = SimpleAgent(str(tmp_path))
        result = agent.explain_file(str(test_file))

        assert "add" in result
        assert "Calculator" in result
        assert "multiply" in result


class TestAgentMode:
    def test_modes(self):
        assert AgentMode.FIX.value == "fix"
        assert AgentMode.EXPLAIN.value == "explain"
        assert AgentMode.REFACTOR.value == "refactor"
