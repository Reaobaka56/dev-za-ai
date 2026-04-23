"""Additional REST API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..agent.code_parser import CodeParser
from ..agent.tools import FileTools

router = APIRouter(prefix="/api/v1")


class ExplainRequest(BaseModel):
    file_path: str


class FixRequest(BaseModel):
    file_path: str
    description: str


class SearchRequest(BaseModel):
    query: str
    directory: str = "."


@router.post("/explain")
async def explain_file(request: ExplainRequest):
    """Explain a file's structure."""
    parser = CodeParser()
    try:
        summary = parser.get_file_summary(request.file_path)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search")
async def search_code(request: SearchRequest):
    """Search code across the project."""
    tools = FileTools()
    result = tools.search_code(request.query, request.directory)
    return {
        "success": result.success,
        "results": result.output.split("\n") if result.success else [],
        "error": result.error
    }


@router.get("/files")
async def list_files(directory: str = ".", pattern: str = "*"):
    """List files in a directory."""
    tools = FileTools()
    result = tools.list_files(directory, pattern)
    return {
        "success": result.success,
        "files": result.output.split("\n") if result.success else [],
        "error": result.error
    }
