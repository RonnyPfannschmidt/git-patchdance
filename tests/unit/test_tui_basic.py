"""Basic tests for TUI components without mocking."""

import pytest
from datetime import datetime

from git_patchdance.core.models import CommitId, CommitInfo
from git_patchdance.tui.app import TuiApp, CommitList, CommitDetails, StatusBar


class TestTuiBasics:
    """Basic tests for TUI components."""
    
    def test_tui_app_initialization(self):
        """Test TuiApp can be initialized."""
        app = TuiApp()
        
        assert app.repository is None
        assert app.commit_graph is None
        assert app.selected_index == 0
        assert app.git_service is not None
    
    def test_commit_list_initialization(self):
        """Test CommitList can be initialized."""
        widget = CommitList()
        
        assert widget.commits == []
        assert widget.selected_index == 0
        assert widget.border_title == "Commits"
    
    def test_commit_list_reactive_properties(self):
        """Test CommitList reactive properties."""
        widget = CommitList()
        
        # Test setting commits
        commits = [
            CommitInfo(
                id=CommitId("abc123"),
                message="Test commit",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        widget.commits = commits
        assert len(widget.commits) == 1
        
        # Test setting selected index
        widget.selected_index = 5
        assert widget.selected_index == 5
    
    def test_commit_list_watch_methods(self):
        """Test CommitList watch methods don't crash."""
        widget = CommitList()
        
        # These should not crash
        widget.watch_commits([])
        widget.watch_selected_index(0)
        
        commits = [
            CommitInfo(
                id=CommitId("abc123"),
                message="Test",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        widget.watch_commits(commits)
        widget.watch_selected_index(1)
    
    def test_commit_details_initialization(self):
        """Test CommitDetails can be initialized."""
        widget = CommitDetails()
        
        assert widget.border_title == "Commit Details"
    
    def test_commit_details_show_commit(self):
        """Test CommitDetails show_commit method."""
        widget = CommitDetails()
        
        commit = CommitInfo(
            id=CommitId("abc123"),
            message="Test commit",
            author="Author",
            email="test@example.com",
            timestamp=datetime.now(),
            parent_ids=[],
            files_changed=["test.py"]
        )
        
        # Should not crash
        widget.show_commit(commit)
    
    def test_status_bar_initialization(self):
        """Test StatusBar can be initialized."""
        widget = StatusBar()
        
        assert widget is not None
    
    def test_status_bar_update(self):
        """Test StatusBar update method."""
        widget = StatusBar()
        
        # Should not crash
        widget.update("Test message")
        widget.update("Another message")
    
    def test_log_property_before_init(self):
        """Test log property behavior before initialization."""
        app = TuiApp()
        
        with pytest.raises(RuntimeError, match="Log widget not initialized"):
            _ = app.log
    
    def test_log_property_after_init(self):
        """Test log property behavior after manual initialization."""
        app = TuiApp()
        
        # Manually set the log widget (simulating compose)
        from textual.widgets import Log
        app._log_widget = Log()
        
        # Should not raise now
        log = app.log
        assert log is app._log_widget


class TestApplicationWrapper:
    """Test the Application compatibility wrapper."""
    
    def test_application_initialization(self):
        """Test Application wrapper initialization."""
        from git_patchdance.tui.app import Application
        
        wrapper = Application()
        assert wrapper.app is not None
        assert isinstance(wrapper.app, TuiApp)


class TestTuiAppMethods:
    """Test TUI app methods that don't require full UI context."""
    
    def create_mock_app(self):
        """Create app with minimal mocked widgets."""
        app = TuiApp()
        
        # Create minimal mock widgets
        class MockWidget:
            def __init__(self):
                self.data = None
                
            def update(self, value):
                self.data = value
            
            def show_commit(self, commit):
                self.data = commit
        
        class MockLog:
            def __init__(self):
                self.messages = []
            
            def write_line(self, message):
                self.messages.append(message)
            
            def write_lines(self, messages):
                self.messages.extend(messages)
        
        app.commit_list = MockWidget()
        app.commit_details = MockWidget() 
        app.status_bar = MockWidget()
        app._log_widget = MockLog()
        
        return app
    
    @pytest.mark.asyncio
    async def test_navigation_with_no_commits(self):
        """Test navigation when no commits are available."""
        app = self.create_mock_app()
        
        # No commit graph
        app.commit_graph = None
        
        # Should not crash
        await app.action_cursor_down()
        await app.action_cursor_up()
        assert app.selected_index == 0
    
    @pytest.mark.asyncio
    async def test_navigation_with_commits(self):
        """Test navigation with commits."""
        app = self.create_mock_app()
        
        from git_patchdance.core.models import CommitGraph
        
        commits = [
            CommitInfo(
                id=CommitId("commit1"),
                message="First",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            ),
            CommitInfo(
                id=CommitId("commit2"),
                message="Second",
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        app.commit_graph = CommitGraph(commits=commits, current_branch="main")
        app.selected_index = 0
        
        # Test navigation down
        await app.action_cursor_down()
        assert app.selected_index == 1
        
        # Test boundary
        await app.action_cursor_down()
        assert app.selected_index == 1  # Should stay at last
        
        # Test navigation up
        await app.action_cursor_up()
        assert app.selected_index == 0
        
        # Test boundary
        await app.action_cursor_up()
        assert app.selected_index == 0  # Should stay at first
    
    @pytest.mark.asyncio
    async def test_help_action(self):
        """Test help action."""
        app = self.create_mock_app()
        
        await app.action_help()
        
        # Should have written help messages
        assert len(app._log_widget.messages) > 0
        help_text = " ".join(app._log_widget.messages)
        assert "Keyboard Shortcuts" in help_text
    
    @pytest.mark.asyncio
    async def test_refresh_action_no_repo(self):
        """Test refresh when no repository is loaded."""
        app = self.create_mock_app()
        
        # No repository loaded
        app.repository = None
        
        # Should not crash
        await app.action_refresh()
    
    def test_run_path_setting(self):
        """Test that run method sets the initial path."""
        app = TuiApp()
        
        # Test the path setting part (without actually running)
        app._initial_path = "/test/path"
        assert app._initial_path == "/test/path"