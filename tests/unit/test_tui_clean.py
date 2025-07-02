"""Clean tests for TUI application logic without mocking."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from git_patchdance.core.errors import GitPatchError
from git_patchdance.core.models import CommitGraph, CommitId, CommitInfo, Repository
from git_patchdance.tui.app import TuiApp


class MockWidget:
    """Simple widget mock for testing app logic."""

    def __init__(self) -> None:
        self.data: Any = None
        self.commits: list[Any] = []
        self.index: int = 0
        self.border_title: str = ""

    def update(self, content: Any) -> None:
        self.data = content

    def show_commit(self, commit: Any) -> None:
        self.data = commit

    def clear(self) -> None:
        self.commits = []

    def append(self, item: Any) -> None:
        self.commits.append(item)


class MockLog:
    """Simple log mock for testing."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def write_line(self, message: str) -> None:
        self.messages.append(message)

    def write_lines(self, messages: list[str]) -> None:
        self.messages.extend(messages)


class TestTuiAppLogic:
    """Test TUI app business logic."""

    def create_test_app(self, path: Path | None = None) -> TuiApp:
        """Create a test app with mocked widgets."""
        if path is None:
            path = Path("/tmp/test")
        app = TuiApp(initial_path=path)

        # Replace widgets with mocks
        app.commit_list = MockWidget()  # type: ignore[assignment]
        app.commit_details = MockWidget()  # type: ignore[assignment]
        app.status_bar = MockWidget()  # type: ignore[assignment]
        app.app_log = MockLog()  # type: ignore[assignment]
        app._log_widget = MockLog()  # type: ignore[attr-defined]

        return app

    @pytest.fixture
    def app(self, tmp_path: Path) -> TuiApp:
        return self.create_test_app(tmp_path)

    def test_app_initialization(self, app: TuiApp) -> None:
        """Test basic app initialization."""

        assert app.repository is None
        assert app.commit_graph is None
        assert app.selected_index == 0
        assert app.git_service is not None
        assert app._initial_path is not None
        assert app._log_widget is not None  # type: ignore[attr-defined]

    def test_log_property_before_init(self, tmp_path: Path) -> None:
        """Test log property before initialization."""
        app = TuiApp(initial_path=tmp_path)

        # App should not have app_log widget before compose
        assert not hasattr(app, "app_log")

    def test_log_property_after_init(self) -> None:
        """Test log property after initialization."""
        app = self.create_test_app()

        # After mocking, app should have app_log
        assert hasattr(app, "app_log")

    @pytest.mark.asyncio
    async def test_load_repository_success(self) -> None:
        """Test successful repository loading."""
        app = self.create_test_app()

        # Create test data
        test_repo = Repository(
            path=Path("/test/repo"),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("abc123"),
        )

        test_commits = [
            CommitInfo(
                id=CommitId("abc123"),
                message="Test commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=(),
                files_changed=["test.py"],
            )
        ]

        test_graph = CommitGraph(
            commits=test_commits, current_branch="main", total_count=1
        )

        # Mock git service
        app.git_service.open_repository = AsyncMock(return_value=test_repo)  # type: ignore[method-assign]
        app.git_service.get_commit_graph = AsyncMock(return_value=test_graph)  # type: ignore[method-assign]

        # Test loading
        await app.load_repository(Path("/test/repo"))

        # Verify state
        assert app.repository == test_repo
        assert app.commit_graph == test_graph
        assert app.selected_index == 0
        assert app.commit_list.commits == test_commits
        assert app.commit_details.data == test_commits[0]  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_load_repository_failure(self) -> None:
        """Test repository loading failure."""
        app = self.create_test_app()

        # Mock failure
        app.git_service.open_repository = AsyncMock(  # type: ignore[method-assign]
            side_effect=GitPatchError("Repository not found")
        )

        # Should not raise error (now handles gracefully)
        await app.load_repository(Path("/nonexistent"))

        # Should log error
        assert len(app.app_log.messages) > 0  # type: ignore[attr-defined]
        assert "Failed to load repository" in app.app_log.messages[0]  # type: ignore[attr-defined]
        # Should update commit details with error info
        assert "Failed to load repository" in app.commit_details.data  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_navigation_down(self) -> None:
        """Test cursor down navigation."""
        app = self.create_test_app()

        commits = [
            CommitInfo(
                id=CommitId(f"commit{i}"),
                message=f"Commit {i}",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=(),
                files_changed=[],
            )
            for i in range(3)
        ]

        app.commit_graph = CommitGraph(commits=commits, current_branch="main")
        app.selected_index = 0

        # Test moving down
        await app.action_cursor_down()
        assert app.selected_index == 1
        assert app.commit_list.index == 1
        assert app.commit_details.data == commits[1]  # type: ignore[attr-defined]

        # Test boundary
        app.selected_index = 2
        await app.action_cursor_down()
        assert app.selected_index == 2  # Should stay at last

    @pytest.mark.asyncio
    async def test_navigation_up(self, app: TuiApp) -> None:
        """Test cursor up navigation."""

        commits = [
            CommitInfo(
                id=CommitId(f"commit{i}"),
                message=f"Commit {i}",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=(),
                files_changed=[],
            )
            for i in range(3)
        ]

        app.commit_graph = CommitGraph(commits=commits, current_branch="main")
        app.selected_index = 2

        # Test moving up
        await app.action_cursor_up()
        assert app.selected_index == 1
        assert app.commit_list.index == 1
        assert app.commit_details.data == commits[1]  # type: ignore[attr-defined]

        # Test boundary
        app.selected_index = 0
        await app.action_cursor_up()
        assert app.selected_index == 0  # Should stay at first

    @pytest.mark.asyncio
    async def test_navigation_with_no_commits(self, app: TuiApp) -> None:
        """Test navigation when no commits are available."""

        # No commit graph
        app.commit_graph = None

        await app.action_cursor_down()
        await app.action_cursor_up()
        assert app.selected_index == 0

        # Empty commit graph
        app.commit_graph = CommitGraph(commits=[], current_branch="main")

        await app.action_cursor_down()
        await app.action_cursor_up()
        assert app.selected_index == 0

    @pytest.mark.asyncio
    async def test_refresh_action(self, app: TuiApp) -> None:
        """Test refresh functionality."""

        # Set up repository
        app.repository = Repository(
            path=Path("/test/repo"),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("abc123"),
        )

        # Mock load_repository
        app.load_repository = AsyncMock()  # type: ignore[method-assign]

        await app.action_refresh()

        # Should reload repository
        app.load_repository.assert_called_once_with(Path("/test/repo"))
        assert "Repository refreshed" in app.app_log.messages  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_refresh_no_repository(self, app: TuiApp) -> None:
        """Test refresh when no repository loaded."""

        app.repository = None

        # Mock git service to simulate loading current directory
        from pathlib import Path

        test_repo = Repository(
            path=Path.cwd(),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("abc123"),
        )
        test_graph = CommitGraph(commits=[], current_branch="main")

        app.git_service.open_repository = AsyncMock(return_value=test_repo)  # type: ignore[method-assign]
        app.git_service.get_commit_graph = AsyncMock(return_value=test_graph)  # type: ignore[method-assign]

        await app.action_refresh()

    def test_run_sets_initial_path(self) -> None:
        """Test that run method sets initial path."""
        path = Path("/test/repo")
        app = TuiApp(initial_path=path)

        assert app._initial_path == path
