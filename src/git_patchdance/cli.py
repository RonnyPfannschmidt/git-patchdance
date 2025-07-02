"""Command-line interface for Git Patchdance."""

import sys
from pathlib import Path

import click

from .core.errors import GitPatchError
from .demo import create_demo_repository
from .git.repository import GitRepository, open_repository
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
@click.option(
    "--demo",
    is_flag=True,
    help="Create and use a demo repository with sample commits for testing",
)
@click.version_option()
def main(path: Path, gui: bool = False, demo: bool = False) -> None:
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
        if demo:
            click.echo("Creating demo repository with sample commits...", err=True)
            git_repository: GitRepository = create_demo_repository()
        else:
            git_repository = open_repository(path)
        app = TuiApp(git_repository=git_repository)
        app.run()
    except KeyboardInterrupt:
        click.echo("\nExiting...")
        sys.exit(0)
    except GitPatchError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
