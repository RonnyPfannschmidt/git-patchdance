"""Clean tests for TUI application logic without mocking."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from git_patchdance.core.models import CommitGraph, CommitId, CommitInfo
from git_patchdance.git.fake_repository import FakeRepository
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

    def create_test_app(self, repository: FakeRepository | None = None) -> TuiApp:
        """Create a test app with mocked widgets."""
        if repository is None:
            repository = FakeRepository.create_test_repository()
        app = TuiApp(git_repository=repository)

        # Replace widgets with mocks
        app.commit_list = MockWidget()  # type: ignore[assignment]
        app.commit_details = MockWidget()  # type: ignore[assignment]
        app.status_bar = MockWidget()  # type: ignore[assignment]
        app.app_log = MockLog()  # type: ignore[assignment]
        app._log_widget = MockLog()  # type: ignore[attr-defined]

        return app

    @pytest.fixture
    def app(self) -> TuiApp:
        return self.create_test_app()

    def test_app_initialization(self, app: TuiApp) -> None:
        """Test basic app initialization."""

        assert app.git_repository is not None
        assert app.commit_graph is None
        assert app.selected_index == 0
        assert app._log_widget is not None  # type: ignore[attr-defined]

    def test_log_property_before_init(self) -> None:
        """Test log property before initialization."""
        fake_repo = FakeRepository.create_test_repository()
        app = TuiApp(git_repository=fake_repo)

        # App should not have app_log widget before compose
        assert not hasattr(app, "app_log")

    def test_log_property_after_init(self) -> None:
        """Test log property after initialization."""
        app = self.create_test_app()

        # After mocking, app should have app_log
        assert hasattr(app, "app_log")

    @pytest.mark.asyncio
    async def test_load_repository_success(self) -> None:
        """Test successful repository data loading."""
        # Create fake repository with test data
        fake_repo = FakeRepository.create_test_repository(
            path=Path("/test/repo"), commit_count=1
        )
        app = self.create_test_app(fake_repo)

        # Test loading repository data
        await app.load_repository_data()

        # Verify state
        assert app.git_repository == fake_repo
        assert app.commit_graph is not None
        assert app.selected_index == 0
        assert len(app.commit_list.commits) == 1
        assert app.commit_details.data == app.commit_graph.commits[0]  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_load_repository_failure(self) -> None:
        """Test repository data loading with error handling."""
        # Create a fake repository that will raise an error
        fake_repo = FakeRepository.create_test_repository(commit_count=0)  # No commits
        app = self.create_test_app(fake_repo)

        # Should handle gracefully when no commits (raises NoCommitsFound)
        await app.load_repository_data()

        # Should log and display error information
        assert len(app.app_log.messages) > 0  # type: ignore[attr-defined]
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

        # Mock load_repository_data
        app.load_repository_data = AsyncMock()  # type: ignore[method-assign]

        await app.action_refresh()

        # Should reload repository data
        app.load_repository_data.assert_called_once()
        assert "Repository refreshed" in app.app_log.messages  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_refresh_no_repository(self, app: TuiApp) -> None:
        """Test refresh functionality (same as with repository)."""

        # Mock load_repository_data
        app.load_repository_data = AsyncMock()  # type: ignore[method-assign]

        await app.action_refresh()

        # Should still refresh since repository is always available now
        app.load_repository_data.assert_called_once()
        assert "Repository refreshed" in app.app_log.messages  # type: ignore[attr-defined]

    def test_repository_injection(self) -> None:
        """Test that repository is properly injected."""
        fake_repo = FakeRepository.create_test_repository(path=Path("/test/repo"))
        app = TuiApp(git_repository=fake_repo)

        assert app.git_repository == fake_repo
        assert app.git_repository.info.path == Path("/test/repo")
