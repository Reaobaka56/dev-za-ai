"""Code understanding via tree-sitter AST parsing."""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from tree_sitter import Language, Parser, Tree, Node
    from tree_sitter_python import language as python_language
    from tree_sitter_javascript import language as js_language
    from tree_sitter_typescript import language as ts_language
    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False
    Language = Parser = Tree = Node = None


@dataclass
class CodeChunk:
    """A chunk of code with metadata."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # function, class, import, docstring, etc.
    name: Optional[str] = None
    language: str = ""


class CodeParser:
    """Parse code files using tree-sitter for structural understanding."""

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
    }

    def __init__(self):
        self.parsers: Dict[str, Parser] = {}
        if TREESITTER_AVAILABLE:
            self._init_parsers()

    def _init_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        try:
            py_lang = Language(python_language)
            js_lang = Language(js_language)
            ts_lang = Language(ts_language)

            for ext in [".py"]:
                parser = Parser(py_lang)
                self.parsers[ext] = parser
            for ext in [".js", ".jsx"]:
                parser = Parser(js_lang)
                self.parsers[ext] = parser
            for ext in [".ts", ".tsx"]:
                parser = Parser(ts_lang)
                self.parsers[ext] = parser
        except Exception as e:
            print(f"Warning: Could not initialize tree-sitter parsers: {e}")

    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse a file and extract structural chunks."""
        path = Path(file_path)
        ext = path.suffix

        if ext not in self.LANGUAGE_MAP:
            return self._fallback_chunks(file_path)

        if not TREESITTER_AVAILABLE or ext not in self.parsers:
            return self._fallback_chunks(file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read().encode("utf-8")

            parser = self.parsers[ext]
            tree = parser.parse(source)

            chunks = []
            root = tree.root_node

            if ext == ".py":
                chunks = self._extract_python_chunks(root, source, file_path)
            else:
                chunks = self._extract_js_ts_chunks(root, source, file_path, ext)

            return chunks if chunks else self._fallback_chunks(file_path)

        except Exception as e:
            return self._fallback_chunks(file_path)

    def _extract_python_chunks(self, root: Any, source: bytes, file_path: str) -> List[CodeChunk]:
        """Extract Python-specific chunks."""
        chunks = []

        def get_text(node):
            return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

        def get_line(node):
            return node.start_point[0] + 1

        for child in root.children:
            if child.type == "function_definition":
                name_node = child.child_by_field_name("name")
                name = get_text(name_node) if name_node else None
                chunks.append(CodeChunk(
                    content=get_text(child),
                    file_path=file_path,
                    start_line=get_line(child),
                    end_line=child.end_point[0] + 1,
                    chunk_type="function",
                    name=name,
                    language="python"
                ))

            elif child.type == "class_definition":
                name_node = child.child_by_field_name("name")
                name = get_text(name_node) if name_node else None
                chunks.append(CodeChunk(
                    content=get_text(child),
                    file_path=file_path,
                    start_line=get_line(child),
                    end_line=child.end_point[0] + 1,
                    chunk_type="class",
                    name=name,
                    language="python"
                ))

            elif child.type in ("import_statement", "import_from_statement"):
                chunks.append(CodeChunk(
                    content=get_text(child),
                    file_path=file_path,
                    start_line=get_line(child),
                    end_line=child.end_point[0] + 1,
                    chunk_type="import",
                    language="python"
                ))

            elif child.type == "expression_statement":
                expr = child.children[0] if child.children else None
                if expr and expr.type == "string":
                    chunks.append(CodeChunk(
                        content=get_text(child),
                        file_path=file_path,
                        start_line=get_line(child),
                        end_line=child.end_point[0] + 1,
                        chunk_type="docstring",
                        language="python"
                    ))

        return chunks

    def _extract_js_ts_chunks(self, root: Any, source: bytes, file_path: str, ext: str) -> List[CodeChunk]:
        """Extract JavaScript/TypeScript chunks."""
        chunks = []
        lang = "typescript" if ext in (".ts", ".tsx") else "javascript"

        def get_text(node):
            return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

        def get_line(node):
            return node.start_point[0] + 1

        def walk(node):
            if node.type in ("function_declaration", "function", "arrow_function"):
                name = None
                if node.type == "function_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = get_text(name_node)
                chunks.append(CodeChunk(
                    content=get_text(node),
                    file_path=file_path,
                    start_line=get_line(node),
                    end_line=node.end_point[0] + 1,
                    chunk_type="function",
                    name=name,
                    language=lang
                ))
            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                name = get_text(name_node) if name_node else None
                chunks.append(CodeChunk(
                    content=get_text(node),
                    file_path=file_path,
                    start_line=get_line(node),
                    end_line=node.end_point[0] + 1,
                    chunk_type="class",
                    name=name,
                    language=lang
                ))
            elif node.type in ("import_statement", "import_declaration"):
                chunks.append(CodeChunk(
                    content=get_text(node),
                    file_path=file_path,
                    start_line=get_line(node),
                    end_line=node.end_point[0] + 1,
                    chunk_type="import",
                    language=lang
                ))

            for child in node.children:
                walk(child)

        walk(root)
        return chunks

    def _fallback_chunks(self, file_path: str, chunk_size: int = 50) -> List[CodeChunk]:
        """Fallback: split file into line-based chunks."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            chunks = []
            for i in range(0, len(lines), chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                content = "".join(chunk_lines)
                chunks.append(CodeChunk(
                    content=content,
                    file_path=file_path,
                    start_line=i + 1,
                    end_line=min(i + chunk_size, len(lines)),
                    chunk_type="block",
                    language=Path(file_path).suffix[1:]
                ))

            return chunks
        except Exception:
            return []

    def get_file_summary(self, file_path: str) -> Dict[str, Any]:
        """Get a summary of a file's structure."""
        chunks = self.parse_file(file_path)

        summary = {
            "file": file_path,
            "language": "",
            "functions": [],
            "classes": [],
            "imports": [],
            "total_lines": 0
        }

        for chunk in chunks:
            if not summary["language"]:
                summary["language"] = chunk.language
            summary["total_lines"] = max(summary["total_lines"], chunk.end_line)

            if chunk.chunk_type == "function" and chunk.name:
                summary["functions"].append(chunk.name)
            elif chunk.chunk_type == "class" and chunk.name:
                summary["classes"].append(chunk.name)
            elif chunk.chunk_type == "import":
                summary["imports"].append(chunk.content.strip())

        return summary
