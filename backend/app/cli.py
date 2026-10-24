import os
import json
import typer
import httpx
from rich.console import Console
from rich.table import Table
from typing import Optional
from pathlib import Path

app = typer.Typer(name="lumen", help="Open agent skills management tool")
console = Console()

API_BASE = os.environ.get("LUMEN_API_BASE", "http://127.0.0.1:8000")
CONFIG_DIR = Path.home() / ".config" / "lumen"
CONFIG_FILE = CONFIG_DIR / "config.json"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_client(access_token: Optional[str] = None) -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return httpx.Client(base_url=f"{API_BASE}/api/v1", headers=headers, timeout=30.0, cookies=None)


@app.command()
def login():
    """Authenticate with the lumen server via OIDC."""
    config = load_config()
    with get_client() as client:
        try:
            resp = client.get("/auth/login")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"[red]Failed to get auth URL: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[blue]Opening browser for authentication...[/blue]")
    console.print(f"[dim]Auth URL: {data['auth_url']}[/dim]")

    import webbrowser
    webbrowser.open(data['auth_url'])

    console.print("\n[yellow]After authenticating, you'll be redirected to a callback URL.[/yellow]")
    console.print("[yellow]Copy the full callback URL and paste it here:[/yellow]")

    callback_url = typer.prompt("Callback URL")

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)

    if "error" in params:
        console.print(f"[red]Authentication failed: {params['error'][0]}[/red]")
        raise typer.Exit(1)

    code = params.get("code", [None])[0]
    state = params.get("state", [None])[0]

    if not code or not state:
        console.print("[red]Invalid callback URL - missing code or state[/red]")
        raise typer.Exit(1)

    with get_client() as client:
        try:
            resp = client.post("/auth/callback", json={
                "code": code,
                "state": state,
                "code_verifier": data["code_verifier"],
            })
            resp.raise_for_status()
            token_data = resp.json()
        except Exception as e:
            console.print(f"[red]Token exchange failed: {e}[/red]")
            raise typer.Exit(1)

    config["access_token"] = token_data["access_token"]
    config["refresh_token"] = token_data.get("refresh_token")
    save_config(config)
    console.print("[green]Authentication successful![/green]")


@app.command()
def logout():
    """Log out and clear stored credentials."""
    config = load_config()
    access_token = config.get("access_token")

    if access_token:
        with get_client(access_token) as client:
            try:
                client.post("/auth/logout")
            except Exception:
                pass

    config.clear()
    save_config(config)
    console.print("[green]Logged out successfully[/green]")


@app.command()
def add(
    source_url: str,
    skill_name: str = typer.Option(..., "--skill", "-s", help="Skill name to install"),
    skill_path: Optional[str] = typer.Option(None, "--path", "-p", help="Path to skill in repo"),
    global_install: bool = typer.Option(False, "--global", "-g", help="Install globally"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install a skill from a GitHub repository."""
    config = load_config()
    access_token = config.get("access_token")
    if not access_token:
        console.print("[red]Not authenticated. Run 'lumen login' first.[/red]")
        raise typer.Exit(1)

    with get_client(access_token) as client:
        try:
            resp = client.post("/skills/install", json={
                "source_url": source_url,
                "skill_name": skill_name,
                "skill_path": skill_path,
                "scope": "global" if global_install else "project",
                "force": force,
            })
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            console.print(f"[red]Install failed: {e.response.json().get('detail', str(e))}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Install failed: {e}[/red]")
            raise typer.Exit(1)

    skill = data["skill"]
    console.print(f"[green]Successfully installed {skill['name']}[/green]")
    console.print(f"  Source: {skill['source_url']}")
    console.print(f"  Scope: {skill['scope']}")
    console.print(f"  Status: {skill['status']}")


@app.command()
def find(
    query: str,
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Filter by owner"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
):
    """Search for skills."""
    config = load_config()
    access_token = config.get("access_token")
    if not access_token:
        console.print("[red]Not authenticated. Run 'lumen login' first.[/red]")
        raise typer.Exit(1)

    with get_client(access_token) as client:
        try:
            resp = client.get("/skills/search", params={"q": query, "owner": owner, "limit": limit})
            resp.raise_for_status()
            results = resp.json()
        except Exception as e:
            console.print(f"[red]Search failed: {e}[/red]")
            raise typer.Exit(1)

    if not results:
        console.print("[yellow]No skills found[/yellow]")
        return

    table = Table("Name", "Owner", "Description", "Source")
    for skill in results:
        table.add_row(
            skill["name"],
            skill["owner"],
            skill.get("description", "")[:50] or "-",
            skill["source_url"],
        )
    console.print(table)


@app.command()
def install(
    global_scope: bool = typer.Option(False, "--global", "-g", help="Use global lock file"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install all skills from lock file (npm ci equivalent)."""
    config = load_config()
    access_token = config.get("access_token")
    if not access_token:
        console.print("[red]Not authenticated. Run 'lumen login' first.[/red]")
        raise typer.Exit(1)

    with get_client(access_token) as client:
        try:
            resp = client.post("/lock/install", json={
                "scope": "global" if global_scope else "project",
                "force": force,
            })
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"[red]Lock install failed: {e}[/red]")
            raise typer.Exit(1)

    results = data.get("results", [])
    for r in results:
        status_color = "green" if r["status"] == "installed" else "red"
        console.print(f"[{status_color}]{r['name']}: {r['status']}[/{status_color}]")
        if "error" in r:
            console.print(f"  [red]Error: {r['error']}[/red]")


@app.command()
def update(
    global_scope: bool = typer.Option(False, "--global", "-g", help="Update global skills"),
    force: bool = typer.Option(False, "--force", "-f", help="Force update"),
):
    """Update installed skills."""
    config = load_config()
    access_token = config.get("access_token")
    if not access_token:
        console.print("[red]Not authenticated. Run 'lumen login' first.[/red]")
        raise typer.Exit(1)

    with get_client(access_token) as client:
        try:
            resp = client.get("/skills", params={"scope": "global" if global_scope else "project"})
            resp.raise_for_status()
            skills_data = resp.json()
        except Exception as e:
            console.print(f"[red]Failed to list skills: {e}[/red]")
            raise typer.Exit(1)

    skills = skills_data.get("items", [])
    if not skills:
        console.print("[yellow]No skills to update[/yellow]")
        return

    for skill in skills:
        with get_client(access_token) as client:
            try:
                resp = client.post(f"/skills/{skill['id']}/update", json={"force": force})
                resp.raise_for_status()
                result = resp.json()
                console.print(f"[green]{skill['name']}: {result['message']}[/green]")
            except Exception as e:
                console.print(f"[red]{skill['name']}: Update failed - {e}[/red]")


@app.command("list")
def list_skills(
    global_scope: bool = typer.Option(False, "--global", "-g", help="List global skills"),
):
    """List installed skills."""
    config = load_config()
    access_token = config.get("access_token")
    if not access_token:
        console.print("[red]Not authenticated. Run 'lumen login' first.[/red]")
        raise typer.Exit(1)

    with get_client(access_token) as client:
        try:
            resp = client.get("/skills", params={"scope": "global" if global_scope else "project"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"[red]List failed: {e}[/red]")
            raise typer.Exit(1)

    skills = data.get("items", [])
    if not skills:
        console.print("[yellow]No skills installed[/yellow]")
        return

    table = Table("Name", "Source", "Scope", "Status")
    for skill in skills:
        table.add_row(
            skill["name"],
            skill["source_url"].split("/")[-2] + "/" + skill["source_url"].split("/")[-1],
            skill["scope"],
            skill["status"],
        )
    console.print(table)


@app.command()
def status():
    """Show authentication status."""
    config = load_config()
    if config.get("access_token"):
        console.print("[green]Authenticated[/green]")
        console.print(f"  API Base: {API_BASE}")
    else:
        console.print("[yellow]Not authenticated[/yellow]")
        console.print(f"  API Base: {API_BASE}")
        console.print("  Run 'lumen login' to authenticate")


@app.callback()
def callback():
    """lumen - Open agent skills management tool"""


if __name__ == "__main__":
    app()
