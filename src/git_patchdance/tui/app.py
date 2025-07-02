"""Textual-based TUI application for Git Patchdance."""

import asyncio
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Log, Static

from ..core.errors import GitPatchError
from ..core.models import CommitGraph, CommitInfo
from ..git.repository import GitRepository


class HelpModal(ModalScreen[None]):
    """Modal screen to display help information."""

    BINDINGS = [
        Binding("escape,q,?", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Create the help modal layout."""
        help_content = Static(
            """[bold]Git Patchdance - Keyboard Shortcuts[/bold]

[dim]Navigation[/dim]
r       Load/refresh repository
j, ↓    Move down (when commits loaded)
k, ↑    Move up (when commits loaded)

[dim]General[/dim]
q       Quit
?       Show/hide this help
Esc     Close this help

[dim]Getting Started[/dim]
1. Press 'r' to load the current directory as a git repository
2. Use j/k or arrow keys to navigate commits
3. Click on commits to select them

[dim]More features coming soon![/dim]

Press [bold]Esc[/bold], [bold]q[/bold], or [bold]?[/bold] to close this help.""",
            id="help-content",
        )
        help_content.border_title = "Help"
        yield help_content


class CommitList(ListView):
    """Widget to display list of commits."""

    commits: reactive[list[CommitInfo]] = reactive([])
    BORDER_TITLE = "Commits"

    def watch_commits(self, commits: list[CommitInfo]) -> None:
        """Update display when commits change."""
        self.clear()
        if not commits:
            self.append(ListItem(Label("No commits found")))
            return

        for commit in commits:
            item_text = f"{commit.id} {commit.summary()[:60]}"
            self.append(ListItem(Label(item_text)))


class CommitDetails(Static):
    """Widget to display details of selected commit."""

    BORDER_TITLE = "Commit Details"

    def __init__(self) -> None:
        super().__init__("Select a commit to view details")

    def show_commit(self, commit: CommitInfo) -> None:
        """Show details for a commit."""
        details = [
            f"Commit: {commit.id.full}",
            f"Author: {commit.author} <{commit.email}>",
            f"Date: {commit.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Parents: {len(commit.parent_ids)}",
            f"Files: {len(commit.files_changed)}",
            "",
            "Message:",
            commit.message,
        ]
        self.update("\n".join(details))


class TuiApp(App[None]):
    """Main TUI application for Git Patchdance."""

    CSS = """
    CommitList {
        width: 1fr;
        border: solid $primary;
    }

    CommitDetails {
        width: 1fr;
        border: solid $primary;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
    }

    Log {
        height: 6;
        border: solid $warning;
    }

    HelpModal {
        align: center middle;
    }

    #help-content {
        width: 60;
        height: 20;
        border: solid $accent;
        background: $surface;
        padding: 1;
    }
    """
    TITLE = "Git Patchdance"
    SUB_TITLE = "Interactive git patch management"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j,down", "cursor_down", "Down"),
        Binding("k,up", "cursor_up", "Up"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "help", "Help"),
    ]

    selected_index: reactive[int] = reactive(0)

    def __init__(self, git_repository: GitRepository, **kwargs: Any):
        super().__init__(**kwargs)
        self.git_repository = git_repository
        self.commit_graph: CommitGraph | None = None

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Horizontal():
            self.commit_list = CommitList()
            yield self.commit_list

            with Vertical():
                self.commit_details = CommitDetails()
                yield self.commit_details

                self.app_log = Log()
                yield self.app_log

        self.status_bar = Label("ready", id="status-bar")
        yield self.status_bar
        yield Footer()

    def write_log(self, message: str) -> None:
        """Write a message to the application log."""
        if self.app_log is not None:
            self.app_log.write_line(message)

    def write_logs(self, messages: list[str]) -> None:
        """Write multiple messages to the application log."""
        if self.app_log is not None:
            self.app_log.write_lines(messages)

    async def on_mount(self) -> None:
        """Initialize the application after compose is complete."""
        self.title = "Git Patchdance"
        self.sub_title = "Interactive git patch management"

        # Show initial loading state
        self.status_bar.update("Ready - Press 'r' to load repository")
        self.commit_details.update(
            "Welcome to Git Patchdance\n\n"
            "Press 'r' to load a repository\nPress '?' for help"
        )

        # Load repository data on startup
        try:
            await self.load_repository_data()
        except Exception as e:
            # Show full traceback during development
            import traceback

            tb = traceback.format_exc()
            self.write_log(f"Error loading repository: {e}")
            self.write_log(f"Full traceback:\n{tb}")
            self.status_bar.update(f"Error: {e}")

    async def load_repository_data(self) -> None:
        """Load repository data."""
        try:
            self.status_bar.update("Loading commits...")

            self.commit_graph = await asyncio.to_thread(
                self.git_repository.get_commit_graph, 50
            )

            self.commit_list.commits = self.commit_graph.commits
            self.selected_index = 0

            if self.commit_graph.commits:
                self.commit_details.show_commit(self.commit_graph.commits[0])
                self.status_bar.update(
                    f"Loaded {len(self.commit_graph.commits)} commits "
                    f"from {self.git_repository.current_branch}"
                )
            else:
                self.commit_details.update("No commits found in repository")
                self.status_bar.update("Repository loaded - no commits found")

        except GitPatchError as e:
            import traceback

            tb = traceback.format_exc()
            self.write_log(f"Failed to load repository: {e}")
            self.write_log(f"Full traceback:\n{tb}")
            self.status_bar.update(f"Error: {e}")
            self.commit_details.update(
                f"Failed to load repository\n\nError: {e}\n\nPress 'r' to try again"
            )
            # Don't re-raise to allow the app to continue running
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            self.write_log(f"Unexpected error: {e}")
            self.write_log(f"Full traceback:\n{tb}")
            self.status_bar.update(f"Unexpected error: {e}")
            self.commit_details.update(
                f"Unexpected error occurred\n\nError: {e}\n\nPress 'r' to try again"
            )

    async def action_cursor_down(self) -> None:
        """Move cursor down."""
        if not self.commit_graph or not self.commit_graph.commits:
            return

        if self.selected_index < len(self.commit_graph.commits) - 1:
            self.selected_index += 1
            self.commit_list.index = self.selected_index
            self.commit_details.show_commit(
                self.commit_graph.commits[self.selected_index]
            )

    async def action_cursor_up(self) -> None:
        """Move cursor up."""
        if not self.commit_graph or not self.commit_graph.commits:
            return

        if self.selected_index > 0:
            self.selected_index -= 1
            self.commit_list.index = self.selected_index
            self.commit_details.show_commit(
                self.commit_graph.commits[self.selected_index]
            )

    async def action_refresh(self) -> None:
        """Refresh repository data."""
        try:
            await self.load_repository_data()
            self.write_log("Repository refreshed")
        except GitPatchError as e:
            self.write_log(f"Failed to refresh repository: {e}")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle commit selection from ListView."""
        if not self.commit_graph or not self.commit_graph.commits:
            return

        if event.list_view is self.commit_list:
            self.selected_index = event.list_view.index or 0
            if 0 <= self.selected_index < len(self.commit_graph.commits):
                self.commit_details.show_commit(
                    self.commit_graph.commits[self.selected_index]
                )

    async def action_help(self) -> None:
        """Show help modal."""
        await self.push_screen(HelpModal())
