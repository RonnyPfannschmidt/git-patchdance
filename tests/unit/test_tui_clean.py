"""Clean tests for TUI application logic without mocking."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from git_patchdance.core.errors import GitPatchError
from git_patchdance.core.models import CommitGraph, CommitId, CommitInfo, Repository
from git_patchdance.tui.app import TuiApp


class MockWidget:
    """Simple widget mock for testing app logic."""

    def __init__(self):
        self.data = None
        self.commits = []
        self.index = 0
        self.border_title = ""

    def update(self, content):
        self.data = content

    def show_commit(self, commit):
        self.data = commit

    def clear(self):
        self.commits = []

    def append(self, item):
        self.commits.append(item)


class MockLog:
    """Simple log mock for testing."""

    def __init__(self):
        self.messages = []

    def write_line(self, message):
        self.messages.append(message)

    def write_lines(self, messages):
        self.messages.extend(messages)


class TestTuiAppLogic:
    """Test TUI app business logic."""

    @pytest.fixture
    def app(self, tmp_path: Path):
        app = TuiApp(initial_path=tmp_path)

        # Replace widgets with mocks
        app.commit_list = MockWidget()
        app.commit_details = MockWidget()
        app.status_bar = MockWidget()
        app._log_widget = MockLog()

        return app

    def test_app_initialization(self, app):
        """Test basic app initialization."""

        assert app.repository is None
        assert app.commit_graph is None
        assert app.selected_index == 0
        assert app.git_service is not None
        assert app._initial_path is None
        assert app._log_widget is None

    def test_log_property_before_init(self, app: TuiApp) -> None:
        """Test log property before initialization."""
        app = TuiApp()

        with pytest.raises(RuntimeError, match="Log widget not initialized"):
            _ = app.log

    def test_log_property_after_init(self):
        """Test log property after initialization."""
        app = self.create_test_app()

        log = app.log
        assert log is app._log_widget

    @pytest.mark.asyncio
    async def test_load_repository_success(self):
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
                parent_ids=[],
                files_changed=["test.py"],
            )
        ]

        test_graph = CommitGraph(
            commits=test_commits, current_branch="main", total_count=1
        )

        # Mock git service
        app.git_service.open_repository = AsyncMock(return_value=test_repo)
        app.git_service.get_commit_graph = AsyncMock(return_value=test_graph)

        # Test loading
        await app.load_repository("/test/repo")

        # Verify state
        assert app.repository == test_repo
        assert app.commit_graph == test_graph
        assert app.selected_index == 0
        assert app.commit_list.commits == test_commits
        assert app.commit_details.data == test_commits[0]

    @pytest.mark.asyncio
    async def test_load_repository_failure(self):
        """Test repository loading failure."""
        app = self.create_test_app()

        # Mock failure
        app.git_service.open_repository = AsyncMock(
            side_effect=GitPatchError("Repository not found")
        )

        # Should not raise error (now handles gracefully)
        await app.load_repository("/nonexistent")

        # Should log error
        assert len(app._log_widget.messages) > 0
        assert "Failed to load repository" in app._log_widget.messages[0]
        # Should update commit details with error info
        assert "Failed to load repository" in app.commit_details.data

    @pytest.mark.asyncio
    async def test_navigation_down(self):
        """Test cursor down navigation."""
        app = self.create_test_app()

        commits = [
            CommitInfo(
                id=CommitId(f"commit{i}"),
                message=f"Commit {i}",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
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
        assert app.commit_details.data == commits[1]

        # Test boundary
        app.selected_index = 2
        await app.action_cursor_down()
        assert app.selected_index == 2  # Should stay at last

    @pytest.mark.asyncio
    async def test_navigation_up(self, app):
        """Test cursor up navigation."""

        commits = [
            CommitInfo(
                id=CommitId(f"commit{i}"),
                message=f"Commit {i}",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
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
        assert app.commit_details.data == commits[1]

        # Test boundary
        app.selected_index = 0
        await app.action_cursor_up()
        assert app.selected_index == 0  # Should stay at first

    @pytest.mark.asyncio
    async def test_navigation_with_no_commits(self, app):
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
    async def test_refresh_action(self, app):
        """Test refresh functionality."""

        # Set up repository
        app.repository = Repository(
            path=Path("/test/repo"),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("abc123"),
        )

        # Mock load_repository
        app.load_repository = AsyncMock()

        await app.action_refresh()

        # Should reload repository
        app.load_repository.assert_called_once_with("/test/repo")
        assert "Repository refreshed" in app._log_widget.messages

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

        app.git_service.open_repository = AsyncMock(return_value=test_repo)
        app.git_service.get_commit_graph = AsyncMock(return_value=test_graph)

        await app.action_refresh()

    def test_run_sets_initial_path(self) -> None:
        """Test that run method sets initial path."""
        path = Path("/test/repo")
        app = TuiApp(initial_path=path)

        assert app._initial_path == path
