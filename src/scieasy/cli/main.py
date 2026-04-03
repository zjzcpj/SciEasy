"""CLI entry point — scieasy serve, run, validate, init, blocks."""

import typer

app = typer.Typer(name="scieasy", help="SciEasy -- AI-native scientific workflow runtime")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI server."""
    typer.echo("Not implemented yet.")


@app.command()
def run(workflow: str = typer.Argument(..., help="Path to workflow YAML")) -> None:
    """Run a workflow headless."""
    typer.echo("Not implemented yet.")


@app.command()
def validate(workflow: str = typer.Argument(..., help="Path to workflow YAML")) -> None:
    """Validate a workflow YAML file."""
    typer.echo("Not implemented yet.")


@app.command()
def init(name: str = "my_project") -> None:
    """Create a new project workspace."""
    typer.echo("Not implemented yet.")


@app.command()
def blocks() -> None:
    """List all installed blocks."""
    typer.echo("Not implemented yet.")
