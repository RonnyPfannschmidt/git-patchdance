"""Command-line interface for Git Patchdance."""

import asyncio
import sys
from pathlib import Path

import click

from .core.errors import GitPatchError
from .git.repository import open_repository
from .tui.app import TuiApp


@click.command()
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to git repository (default: current directory)",
    default=".",
)
@click.option(
    "--gui",
    is_flag=True,
    help="Launch GUI interface (not yet implemented)",
)
@click.version_option()
def main(path: Path, gui: bool = False) -> None:
    """Interactive terminal tool for git patch management.

    Git Patchdance allows you to interactively move patches between commits,
    split commits, and reorganize git history through an intuitive interface.
    """
    if gui:
        click.echo("GUI interface not yet implemented. Using TUI.", err=True)
    if not sys.stdout.isatty():
        click.echo("This application requires a terminal interface to run.", err=True)
        sys.exit(1)
    try:
        asyncio.run(run_tui(path))
    except KeyboardInterrupt:
        click.echo("\nExiting...")
        sys.exit(0)
    except GitPatchError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


async def run_tui(path: Path) -> None:
    """Run the TUI application."""

    git_repository = open_repository(path)
    app = TuiApp(git_repository=git_repository)
    await app.run_async()


if __name__ == "__main__":
    main()
