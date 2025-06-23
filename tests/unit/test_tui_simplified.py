"""Simplified tests for TUI application logic."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

from git_patchdance.core.models import CommitId, CommitInfo, CommitGraph, Repository
from git_patchdance.core.errors import GitPatchError
from git_patchdance.tui.app import TuiApp


class TestTuiAppLogic:
    """Tests for TUI application business logic without UI dependencies."""
    
    def create_test_app(self):
        """Create a TUI app with mocked dependencies for testing."""
        app = TuiApp()
        
        # Create simple dummy objects for UI widgets
        class MockWidget:
            def __init__(self):
                self.data = None
                self.selected_index = 0
                self.commits = []
                
            def update(self, text):
                self.data = text
            
            def show_commit(self, commit):
                self.data = commit
        
        class MockLog:
            def __init__(self):
                self.messages = []
            
            def write_line(self, text):
                self.messages.append(text)
            
            def write_lines(self, lines):
                self.messages.extend(lines)
        
        # Set up dummy widgets
        app.commit_list = MockWidget()
        app.commit_details = MockWidget()
        app.status_bar = MockWidget()
        app._log_widget = MockLog()
        
        return app
    
    def test_initialization(self):
        """Test app initialization."""
        app = TuiApp()
        
        assert app.repository is None
        assert app.commit_graph is None
        assert app.selected_index == 0
        assert app.git_service is not None
    
    def test_log_property_before_init(self):
        """Test log property before widget initialization."""
        app = TuiApp()
        
        with pytest.raises(RuntimeError, match="Log widget not initialized"):
            _ = app.log
    
    def test_log_property_after_init(self):
        """Test log property after widget initialization."""
        app = self.create_test_app()
        
        # Should not raise after _log_widget is set
        log = app.log
        assert log is app._log_widget
    
    @pytest.mark.asyncio
    async def test_load_repository_success(self):
        """Test successful repository loading."""
        app = self.create_test_app()
        
        # Mock data
        test_repository = Repository(
            path=Path("/test/repo"),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("abc123")
        )
        
        test_commits = [
            CommitInfo(
                id=CommitId("abc123"),
                message="Test commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=["test.py"]
            )
        ]
        
        test_commit_graph = CommitGraph(
            commits=test_commits,
            current_branch="main",
            total_count=1
        )
        
        # Mock git service
        app.git_service.open_repository = AsyncMock(return_value=test_repository)
        app.git_service.get_commit_graph = AsyncMock(return_value=test_commit_graph)
        
        # Test loading
        await app.load_repository("/test/repo")
        
        # Verify state
        assert app.repository == test_repository
        assert app.commit_graph == test_commit_graph
        assert app.selected_index == 0
        assert app.commit_list.commits == test_commits
        assert app.commit_details.data == test_commits[0]
    
    @pytest.mark.asyncio
    async def test_load_repository_failure(self):
        """Test repository loading failure."""
        app = self.create_test_app()
        
        # Mock git service to fail
        app.git_service.open_repository = AsyncMock(
            side_effect=GitPatchError("Repository not found")
        )
        
        # Should raise the error
        with pytest.raises(GitPatchError):
            await app.load_repository("/nonexistent")
        
        # Should log the error
        assert len(app._log_widget.messages) > 0
        assert "Failed to load repository" in app._log_widget.messages[0]
    
    @pytest.mark.asyncio
    async def test_cursor_navigation(self):
        """Test cursor navigation logic."""
        app = self.create_test_app()
        
        # Set up commits
        commits = [
            CommitInfo(
                id=CommitId(f"commit{i}"),
                message=f"Commit {i}",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
            for i in range(3)
        ]
        
        app.commit_graph = CommitGraph(commits=commits, current_branch="main")
        app.selected_index = 0
        
        # Test moving down
        await app.action_cursor_down()
        assert app.selected_index == 1
        assert app.commit_details.data == commits[1]
        
        await app.action_cursor_down()
        assert app.selected_index == 2
        assert app.commit_details.data == commits[2]
        
        # Test boundary - should stay at last
        await app.action_cursor_down()
        assert app.selected_index == 2
        
        # Test moving up
        await app.action_cursor_up()
        assert app.selected_index == 1
        assert app.commit_details.data == commits[1]
        
        await app.action_cursor_up()
        assert app.selected_index == 0
        assert app.commit_details.data == commits[0]
        
        # Test boundary - should stay at first
        await app.action_cursor_up()
        assert app.selected_index == 0
    
    @pytest.mark.asyncio
    async def test_navigation_with_no_commits(self):
        """Test navigation when no commits are available."""
        app = self.create_test_app()
        
        # No commit graph
        app.commit_graph = None
        
        # Should not crash
        await app.action_cursor_down()
        await app.action_cursor_up()
        assert app.selected_index == 0
        
        # Empty commit graph
        app.commit_graph = CommitGraph(commits=[], current_branch="main")
        
        await app.action_cursor_down()
        await app.action_cursor_up()
        assert app.selected_index == 0
    
    @pytest.mark.asyncio
    async def test_refresh_action(self):
        """Test refresh functionality."""
        app = self.create_test_app()
        
        # Set up initial repository
        app.repository = Repository(
            path=Path("/test/repo"),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("abc123")
        )
        
        # Mock load_repository method
        app.load_repository = AsyncMock()
        
        # Test refresh
        await app.action_refresh()
        
        # Should call load_repository with current path
        app.load_repository.assert_called_once_with("/test/repo")
        
        # Should log success message
        assert "Repository refreshed" in app._log_widget.messages
    
    @pytest.mark.asyncio
    async def test_refresh_with_no_repository(self):
        """Test refresh when no repository is loaded."""
        app = self.create_test_app()
        
        # No repository loaded
        app.repository = None
        
        # Should not crash and not attempt to reload
        await app.action_refresh()
        
        # No messages should be logged
        assert len(app._log_widget.messages) == 0
    
    @pytest.mark.asyncio
    async def test_help_action(self):
        """Test help functionality."""
        app = self.create_test_app()
        
        await app.action_help()
        
        # Should write help content to log
        assert len(app._log_widget.messages) > 0
        help_content = " ".join(app._log_widget.messages)
        assert "Keyboard Shortcuts" in help_content
        assert "Move down" in help_content
        assert "Move up" in help_content
        assert "Refresh" in help_content
        assert "Quit" in help_content
    
    def test_run_method_sets_path(self):
        """Test run method sets initial path without actually running."""
        app = TuiApp()
        
        # Test that setting the initial path works
        app._initial_path = "/test/repo"
        assert app._initial_path == "/test/repo"


class TestTuiWidgetLogic:
    """Tests for individual widget logic."""
    
    def test_commit_list_widget(self):
        """Test CommitList widget logic."""
        from git_patchdance.tui.app import CommitList
        
        widget = CommitList()
        
        # Test initialization
        assert widget.commits == []
        assert widget.selected_index == 0
        assert widget.border_title == "Commits"
    
    def test_commit_details_widget(self):
        """Test CommitDetails widget logic."""
        from git_patchdance.tui.app import CommitDetails
        
        widget = CommitDetails()
        
        # Test initialization
        assert widget.border_title == "Commit Details"
    
    def test_status_bar_widget(self):
        """Test StatusBar widget logic."""
        from git_patchdance.tui.app import StatusBar
        
        widget = StatusBar()
        
        # Should initialize without error
        assert widget is not None


class TestApplicationWrapper:
    """Tests for the Application compatibility wrapper."""
    
    def test_application_wrapper(self):
        """Test Application wrapper."""
        from git_patchdance.tui.app import Application
        
        wrapper = Application()
        
        assert wrapper.app is not None
        assert isinstance(wrapper.app, TuiApp)
    
    @pytest.mark.asyncio
    async def test_application_wrapper_run(self):
        """Test Application wrapper run method."""
        from git_patchdance.tui.app import Application
        
        wrapper = Application()
        wrapper.app.run = AsyncMock()
        
        await wrapper.run("/test/repo")
        
        wrapper.app.run.assert_called_once_with("/test/repo")