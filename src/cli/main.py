"""CLI interface for the AI Dev Agent."""
import os
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..agent.core import AgentOrchestrator, AgentMode, SimpleAgent
from ..agent.llm import LLMClient
from ..agent.memory import AgentMemory

app = typer.Typer(
    name="agent",
    help="🤖 AI Dev Agent - Your intelligent coding assistant",
    rich_markup_mode="rich"
)
console = Console()


def get_agent() -> AgentOrchestrator:
    """Get or create agent instance."""
    llm = LLMClient()
    memory = AgentMemory(llm_client=llm)
    return AgentOrchestrator(
        root_dir=os.getcwd(),
        llm_client=llm,
        memory=memory
    )


@app.command()
def explain(
    file_path: str = typer.Argument(..., help="Path to the file to explain"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Show raw output without formatting")
):
    """📖 Explain what a file does."""
    console.print(Panel(f"[bold blue]Explaining:[/bold blue] {file_path}", border_style="blue"))

    # Quick structural explanation
    simple = SimpleAgent()
    summary = simple.explain_file(file_path)
    console.print(summary)

    # Deep LLM explanation
    console.print("\n[dim]Getting deep analysis...[/dim]\n")

    agent = get_agent()

    async def run():
        async for chunk in agent.run(AgentMode.EXPLAIN, target=file_path):
            console.print(chunk, end="")

    asyncio.run(run())
    console.print("\n")


@app.command()
def fix(
    file_path: str = typer.Argument(..., help="File to fix"),
    description: str = typer.Option("", "--description", "-d", help="Description of the bug"),
    no_commit: bool = typer.Option(False, "--no-commit", help="Don't auto-commit changes")
):
    """🔧 Fix bugs in a file."""
    console.print(Panel(
        f"[bold red]Fixing:[/bold red] {file_path}\n[dim]{description}[/dim]",
        border_style="red"
    ))

    agent = get_agent()

    async def run():
        async for chunk in agent.run(AgentMode.FIX, target=file_path, description=description):
            console.print(chunk, end="")

    asyncio.run(run())
    console.print("\n[green]✅ Fix complete![/green]\n")


@app.command()
def refactor(
    file_path: str = typer.Argument(..., help="File to refactor"),
    description: str = typer.Option("", "--description", "-d", help="What to improve")
):
    """♻️  Refactor code for better quality."""
    console.print(Panel(
        f"[bold yellow]Refactoring:[/bold yellow] {file_path}",
        border_style="yellow"
    ))

    agent = get_agent()

    async def run():
        async for chunk in agent.run(AgentMode.REFACTOR, target=file_path, description=description):
            console.print(chunk, end="")

    asyncio.run(run())
    console.print("\n[green]✅ Refactor complete![/green]\n")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question about the codebase")
):
    """❓ Ask a question about the codebase."""
    console.print(Panel(f"[bold green]Question:[/bold green] {question}", border_style="green"))

    agent = get_agent()

    async def run():
        async for chunk in agent.run(AgentMode.ASK, description=question):
            console.print(chunk, end="")

    asyncio.run(run())
    console.print("\n")


@app.command()
def index(
    directory: str = typer.Option(".", "--dir", "-d", help="Directory to index"),
    clear: bool = typer.Option(False, "--clear", "-c", help="Clear existing index first")
):
    """📚 Index the project for better code understanding."""
    console.print(Panel("[bold cyan]Indexing Project...[/bold cyan]", border_style="cyan"))

    llm = LLMClient()
    memory = AgentMemory(llm_client=llm)

    if clear:
        memory.clear()
        console.print("[yellow]Cleared existing index[/yellow]")

    async def run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Indexing files...", total=None)
            result = await memory.index_project(directory)
            progress.update(task, completed=True)

        table = Table(title="Index Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in result.items():
            table.add_row(key, str(value))

        console.print(table)

    asyncio.run(run())


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    n: int = typer.Option(5, "--results", "-n", help="Number of results")
):
    """🔍 Search the code memory."""
    console.print(Panel(f"[bold magenta]Searching:[/bold magenta] {query}", border_style="magenta"))

    llm = LLMClient()
    memory = AgentMemory(llm_client=llm)

    async def run():
        results = await memory.search(query, n)

        if not results:
            console.print("[dim]No results found. Try indexing first with `agent index`[/dim]")
            return

        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            content = result["content"][:300]

            panel = Panel(
                f"[dim]{meta['file_path']}:{meta['start_line']}-{meta['end_line']}[/dim]\n"
                f"[cyan]Type:[/cyan] {meta['chunk_type']} | "
                f"[cyan]Name:[/cyan] {meta.get('name', 'N/A')}\n\n"
                f"{content}...",
                title=f"Result {i} (score: {result['distance']:.3f})",
                border_style="blue"
            )
            console.print(panel)

    asyncio.run(run())


@app.command()
def chat():
    """💬 Interactive chat mode."""
    console.print(Panel(
        "[bold green]🤖 AI Dev Agent Chat[/bold green]\n"
        "[dim]Type 'exit' or 'quit' to leave[/dim]",
        border_style="green"
    ))

    agent = get_agent()

    async def interactive():
        while True:
            user_input = console.input("[bold blue]You:[/bold blue] ")

            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            console.print("[bold green]Agent:[/bold green] ", end="")

            async for chunk in agent.run(AgentMode.CHAT, description=user_input):
                console.print(chunk, end="")

            console.print("\n")

    asyncio.run(interactive())


@app.command()
def status():
    """📊 Show agent status and memory stats."""
    llm = LLMClient()
    memory = AgentMemory(llm_client=llm)

    stats = memory.get_stats()

    table = Table(title="🤖 AI Dev Agent Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", "✅ Ready")
    table.add_row("Memory Status", stats.get("status", "unknown"))
    table.add_row("Indexed Chunks", str(stats.get("count", 0)))
    table.add_row("Working Directory", os.getcwd())
    table.add_row("LLM Model", os.getenv("LLM_MODEL", "gpt-4o-mini"))

    console.print(table)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", "-v", help="Show version")
):
    """🤖 AI Dev Agent - Intelligent coding assistant with memory, tools, and reasoning."""
    if version:
        console.print("AI Dev Agent v1.0.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
