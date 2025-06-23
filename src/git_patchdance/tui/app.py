"""Textual-based TUI application for Git Patchdance."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Log, Static

from ..core.errors import GitPatchError
from ..core.models import CommitGraph, CommitInfo, Repository
from ..git.service import GitServiceImpl


class CommitList(Static):
    """Widget to display list of commits."""

    commits: reactive[list[CommitInfo]] = reactive([])
    selected_index: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Commits"

    def watch_commits(self, commits: list[CommitInfo]) -> None:
        """Update display when commits change."""
        if not commits:
            self.update("No commits found")
            return

        lines = []
        for i, commit in enumerate(commits):
            marker = ">" if i == self.selected_index else " "
            lines.append(f"{marker} {commit.id.short()} {commit.summary()[:60]}")

        self.update("\n".join(lines))

    def watch_selected_index(self, index: int) -> None:
        """Update display when selection changes."""
        self.watch_commits(self.commits)


class CommitDetails(Static):
    """Widget to display details of selected commit."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Commit Details"
        self.update("Select a commit to view details")

    def show_commit(self, commit: CommitInfo) -> None:
        """Show details for a commit."""
        details = [
            f"Commit: {commit.id.full()}",
            f"Author: {commit.author} <{commit.email}>",
            f"Date: {commit.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Parents: {len(commit.parent_ids)}",
            f"Files: {len(commit.files_changed)}",
            "",
            "Message:",
            commit.message,
        ]
        self.update("\n".join(details))


class StatusBar(Static):
    """Widget to display status information."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update("Ready")


class TuiApp(App):
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
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j,down", "cursor_down", "Down"),
        Binding("k,up", "cursor_up", "Up"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.git_service = GitServiceImpl()
        self.repository: Repository | None = None
        self.commit_graph: CommitGraph | None = None
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Horizontal():
            self.commit_list = CommitList()
            yield self.commit_list

            with Vertical():
                self.commit_details = CommitDetails()
                yield self.commit_details

                self.log = Log()
                yield self.log

        self.status_bar = StatusBar()
        yield self.status_bar
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the application."""
        self.title = "Git Patchdance"
        self.sub_title = "Interactive git patch management"

        try:
            await self.load_repository()
        except GitPatchError as e:
            self.log.write_line(f"Error loading repository: {e}")
            self.status_bar.update(f"Error: {e}")

    async def load_repository(self, path: str | None = None) -> None:
        """Load git repository."""
        try:
            self.status_bar.update("Loading repository...")
            self.repository = await self.git_service.open_repository(path)

            self.status_bar.update("Loading commits...")
            self.commit_graph = await self.git_service.get_commit_graph(
                self.repository, limit=50
            )

            self.commit_list.commits = self.commit_graph.commits
            self.selected_index = 0

            if self.commit_graph.commits:
                self.commit_details.show_commit(self.commit_graph.commits[0])

            self.status_bar.update(
                f"Loaded {len(self.commit_graph.commits)} commits "
                f"from {self.repository.current_branch}"
            )

        except GitPatchError as e:
            self.log.write_line(f"Failed to load repository: {e}")
            self.status_bar.update("Failed to load repository")
            raise

    async def action_cursor_down(self) -> None:
        """Move cursor down."""
        if not self.commit_graph or not self.commit_graph.commits:
            return

        if self.selected_index < len(self.commit_graph.commits) - 1:
            self.selected_index += 1
            self.commit_list.selected_index = self.selected_index
            self.commit_details.show_commit(
                self.commit_graph.commits[self.selected_index]
            )

    async def action_cursor_up(self) -> None:
        """Move cursor up."""
        if not self.commit_graph or not self.commit_graph.commits:
            return

        if self.selected_index > 0:
            self.selected_index -= 1
            self.commit_list.selected_index = self.selected_index
            self.commit_details.show_commit(
                self.commit_graph.commits[self.selected_index]
            )

    async def action_refresh(self) -> None:
        """Refresh repository data."""
        if self.repository:
            try:
                await self.load_repository(str(self.repository.path))
                self.log.write_line("Repository refreshed")
            except GitPatchError as e:
                self.log.write_line(f"Failed to refresh: {e}")

    async def action_help(self) -> None:
        """Show help."""
        help_text = [
            "Git Patchdance - Keyboard Shortcuts",
            "",
            "j, ↓    Move down",
            "k, ↑    Move up",
            "r       Refresh repository",
            "q       Quit",
            "?       Show this help",
            "",
            "More features coming soon!",
        ]
        self.log.write_lines(help_text)

    async def run(self, repository_path: str | None = None) -> None:
        """Run the TUI application."""
        if repository_path:
            # Store path for loading after mount
            self._initial_path = repository_path

        await super().run_async()


# For backwards compatibility with existing imports
class Application:
    """Compatibility wrapper for the TUI application."""

    def __init__(self):
        self.app = TuiApp()

    async def run(self, repository_path: str | None = None) -> None:
        await self.app.run(repository_path)
