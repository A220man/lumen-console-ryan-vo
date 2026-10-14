import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
from pathlib import Path

app = typer.Typer(name="lumen", help="Open agent skills management tool")
console = Console()


@app.command()
def add(
    source_url: str,
    skill_name: str = typer.Option(..., "--skill", "-s", help="Skill name to install"),
    skill_path: Optional[str] = typer.Option(None, "--path", "-p", help="Path to skill in repo"),
    global_install: bool = typer.Option(False, "--global", "-g", help="Install globally"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install a skill from a GitHub repository."""
    console.print(f"[blue]Installing {skill_name} from {source_url}[/blue]")
    console.print("[yellow]CLI not fully implemented - use web UI or API[/yellow]")


@app.command()
def find(
    query: str,
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Filter by owner"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
):
    """Search for skills."""
    console.print(f"[blue]Searching for: {query}[/blue]")
    console.print("[yellow]CLI not fully implemented - use web UI or API[/yellow]")


@app.command()
def install(
    global_scope: bool = typer.Option(False, "--global", "-g", help="Use global lock file"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install all skills from lock file (npm ci equivalent)."""
    console.print("[blue]Installing from lock file[/blue]")
    console.print("[yellow]CLI not fully implemented - use web UI or API[/yellow]")


@app.command()
def update(
    global_scope: bool = typer.Option(False, "--global", "-g", help="Update global skills"),
    force: bool = typer.Option(False, "--force", "-f", help="Force update"),
):
    """Update installed skills."""
    console.print("[blue]Checking for updates[/blue]")
    console.print("[yellow]CLI not fully implemented - use web UI or API[/yellow]")


@app.command()
def list(
    global_scope: bool = typer.Option(False, "--global", "-g", help="List global skills"),
):
    """List installed skills."""
    console.print("[blue]Installed skills:[/blue]")
    table = Table("Name", "Source", "Scope", "Status")
    console.print(table)
    console.print("[yellow]CLI not fully implemented - use web UI or API[/yellow]")


@app.callback()
def callback():
    """lumen - Open agent skills management tool"""


if __name__ == "__main__":
    app()