import asyncio

import typer
from rich.console import Console
from rich.table import Table

from apps.crl.core.models import ArtifactType, BaseArtifact
from apps.crl.services.rae_client import RAEClient

app = typer.Typer(help="RAE-CRL: Cognitive Research Loop CLI")
console = Console()
rae = RAEClient()


@app.command()
def init(project: str):
    """Initialize a new research project context locally."""
    console.print(f"[green]Initialized project context: {project}[/green]")
    # In V2 this would persist config locally


@app.command()
def add(type: ArtifactType, title: str, description: str, project: str):
    """Add a new research artifact."""
    artifact = BaseArtifact(
        type=type, title=title, description=description, project_id=project
    )

    success = asyncio.run(rae.store_artifact(artifact))
    if success:
        console.print(f"[bold green]Stored {type.value}:[/bold green] {title}")
    else:
        console.print(
            "[bold red]Failed to store artifact (Check RAE connection)[/bold red]"
        )


@app.command()
def query(text: str, project: str):
    """Semantic search over research history."""
    results = asyncio.run(rae.query_artifacts(text, project))

    table = Table(title=f"Research Memory: {text}")
    table.add_column("Score", style="cyan")
    table.add_column("Content")

    for r in results:
        table.add_row(str(round(r.get("score", 0), 2)), r.get("content", "")[:200])

    console.print(table)


if __name__ == "__main__":
    app()
