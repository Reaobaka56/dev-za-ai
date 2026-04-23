"""Tests for agent tools."""
import os
import tempfile
import pytest
from src.agent.tools import FileTools, TerminalTools, ToolResult


class TestFileTools:
    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    return 'world'\n")
            temp_path = f.name

        tools = FileTools()
        result = tools.read_file(temp_path)

        assert result.success
        assert "def hello" in result.output

        os.unlink(temp_path)

    def test_write_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tools = FileTools(tmpdir)
            result = tools.write_file("test.py", "x = 1\n")

            assert result.success
            assert os.path.exists(os.path.join(tmpdir, "test.py"))

    def test_apply_patch(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def old():\n    pass\n")
            temp_path = f.name

        tools = FileTools()
        result = tools.apply_patch(
            temp_path,
            "def old():\n    pass",
            "def new():\n    return 42"
        )

        assert result.success

        with open(temp_path) as f:
            content = f.read()
        assert "def new" in content

        os.unlink(temp_path)


class TestTerminalTools:
    def test_run_command(self):
        tools = TerminalTools()
        result = tools.run_command("echo hello")

        assert result.success
        assert "hello" in result.output
