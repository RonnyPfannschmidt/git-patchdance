"""Tests for the TUI application."""

import pytest
from datetime import datetime
from pathlib import Path

from git_patchdance.core.models import CommitId, CommitInfo, CommitGraph, Repository
from git_patchdance.core.errors import GitPatchError
from git_patchdance.tui.app import TuiApp, CommitList, CommitDetails, StatusBar


class TestCommitList:
    """Tests for the CommitList widget."""
    
    def test_commit_list_initialization(self):
        """Test CommitList widget initialization."""
        commit_list = CommitList()
        assert commit_list.commits == []
        assert commit_list.selected_index == 0
        assert commit_list.border_title == "Commits"
    
    def test_commit_list_empty_commits(self):
        """Test CommitList with no commits."""
        commit_list = CommitList()
        commit_list.watch_commits([])
        # The update method is called but we can't easily test the content
        # without a more complex test setup
    
    def test_commit_list_with_commits(self):
        """Test CommitList with commits."""
        commits = [
            CommitInfo(
                id=CommitId("a1b2c3d4e5f6789012345678901234567890abcd"),
                message="First commit\n\nDetailed description",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=["file1.txt"]
            ),
            CommitInfo(
                id=CommitId("b2c3d4e5f6789012345678901234567890abcdef"),
                message="Second commit",
                author="Test Author",
                email="test@example.com", 
                timestamp=datetime.now(),
                parent_ids=[CommitId("a1b2c3d4e5f6789012345678901234567890abcd")],
                files_changed=["file2.txt"]
            )
        ]
        
        commit_list = CommitList()
        commit_list.commits = commits
        commit_list.watch_commits(commits)
        
        assert len(commit_list.commits) == 2
    
    def test_commit_list_selection_change(self):
        """Test CommitList selection changes."""
        commit_list = CommitList()
        commit_list.selected_index = 1
        commit_list.watch_selected_index(1)
        
        assert commit_list.selected_index == 1


class TestCommitDetails:
    """Tests for the CommitDetails widget."""
    
    def test_commit_details_initialization(self):
        """Test CommitDetails widget initialization."""
        details = CommitDetails()
        assert details.border_title == "Commit Details"
    
    def test_commit_details_show_commit(self):
        """Test showing commit details."""
        commit = CommitInfo(
            id=CommitId("a1b2c3d4e5f6789012345678901234567890abcd"),
            message="Test commit message",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            parent_ids=[],
            files_changed=["file1.txt", "file2.txt"]
        )
        
        details = CommitDetails()
        details.show_commit(commit)
        # The update method is called but we can't easily test the content
        # without a more complex test setup


class TestStatusBar:
    """Tests for the StatusBar widget."""
    
    def test_status_bar_initialization(self):
        """Test StatusBar widget initialization."""
        status_bar = StatusBar()
        # Initial state should be "Ready"


class TestTuiApp:
    """Tests for the main TUI application."""
    
    def _create_dummy_widgets(self):
        """Create dummy widgets for testing."""
        class DummyWidget:
            def __init__(self):
                self.selected_index = 0
                self.commits = []
                self.last_commit = None
            
            def show_commit(self, commit):
                self.last_commit = commit
            
            def update(self, text):
                self.last_update = text
        
        class DummyLog:
            def __init__(self):
                self.lines = []
            
            def write_line(self, text):
                self.lines.append(text)
            
            def write_lines(self, lines):
                self.lines.extend(lines)
        
        return DummyWidget, DummyLog
    
    def test_tui_app_initialization(self):
        """Test TuiApp initialization."""
        app = TuiApp()
        
        assert app.repository is None
        assert app.commit_graph is None
        assert app.selected_index == 0
        assert app._initial_path is None
        assert app.git_service is not None
        assert app._log_widget is None
    
    def test_tui_app_log_property_before_compose(self):
        """Test that log property raises error before compose."""
        app = TuiApp()
        
        # Before compose, log should raise an error
        with pytest.raises(RuntimeError, match="Log widget not initialized"):
            _ = app.log
    
    @pytest.mark.asyncio
    async def test_load_repository_success(self):
        """Test successful repository loading logic."""
        app = TuiApp()
        
        # Create test data
        mock_repository = Repository(
            path=Path("/test/repo"),
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        )
        
        mock_commits = [
            CommitInfo(
                id=CommitId("a1b2c3d4e5f6789012345678901234567890abcd"),
                message="Test commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=["file1.txt"]
            )
        ]
        
        mock_commit_graph = CommitGraph(
            commits=mock_commits,
            current_branch="main",
            total_count=1
        )
        
        # Mock git service methods
        app.git_service.open_repository = AsyncMock(return_value=mock_repository)
        app.git_service.get_commit_graph = AsyncMock(return_value=mock_commit_graph)
        
        # Create dummy widgets to satisfy the load_repository method
        DummyWidget, DummyLog = self._create_dummy_widgets()
        
        app.commit_list = DummyWidget()
        app.commit_details = DummyWidget()
        app.status_bar = DummyWidget()
        
        # Load repository
        await app.load_repository("/test/repo")
        
        # Verify results
        assert app.repository == mock_repository
        assert app.commit_graph == mock_commit_graph
        assert app.selected_index == 0
        
        # Verify service calls
        app.git_service.open_repository.assert_called_once_with("/test/repo")
        app.git_service.get_commit_graph.assert_called_once_with(mock_repository, limit=50)
    
    @pytest.mark.asyncio
    async def test_load_repository_failure(self):
        """Test repository loading failure."""
        app = TuiApp()
        
        # Mock git service to raise an error
        app.git_service.open_repository = AsyncMock(side_effect=GitPatchError("Repository not found"))
        
        # Create dummy widgets
        class DummyWidget:
            def update(self, text):
                pass
        
        class DummyLog:
            def write_line(self, text):
                pass
        
        app.status_bar = DummyWidget()
        app._log_widget = DummyLog()
        
        # Load repository should raise exception
        with pytest.raises(GitPatchError):
            await app.load_repository("/nonexistent/repo")
    
    @pytest.mark.asyncio
    async def test_cursor_navigation_up(self):
        """Test cursor up navigation."""
        app = TuiApp()
        list(app.compose())
        
        # Mock commit graph with multiple commits
        commits = [
            CommitInfo(
                id=CommitId("commit1"),
                message="First commit", 
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            ),
            CommitInfo(
                id=CommitId("commit2"),
                message="Second commit",
                author="Author", 
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        app.commit_graph = CommitGraph(commits=commits, current_branch="main")
        app.selected_index = 1
        
        # Mock widgets
        app.commit_list = MagicMock()
        app.commit_details = MagicMock()
        
        # Test cursor up
        await app.action_cursor_up()
        
        assert app.selected_index == 0
        app.commit_details.show_commit.assert_called_once_with(commits[0])
    
    @pytest.mark.asyncio
    async def test_cursor_navigation_boundaries(self):
        """Test cursor navigation at boundaries."""
        app = TuiApp()
        list(app.compose())
        
        # Test with empty commit graph
        app.commit_graph = None
        await app.action_cursor_down()
        await app.action_cursor_up()
        # Should not crash
        
        # Test with single commit
        commits = [
            CommitInfo(
                id=CommitId("commit1"),
                message="Only commit",
                author="Author",
                email="test@example.com", 
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        app.commit_graph = CommitGraph(commits=commits, current_branch="main")
        app.selected_index = 0
        
        # Try to go down from last item
        await app.action_cursor_down()
        assert app.selected_index == 0  # Should stay at 0
        
        # Try to go up from first item  
        await app.action_cursor_up()
        assert app.selected_index == 0  # Should stay at 0
    
    @pytest.mark.asyncio
    @patch('git_patchdance.tui.app.GitServiceImpl')
    async def test_refresh_action(self, mock_git_service_class):
        """Test refresh action."""
        # Setup mocks
        mock_git_service = AsyncMock()
        mock_git_service_class.return_value = mock_git_service
        
        app = TuiApp()
        list(app.compose())
        
        # Set up repository
        app.repository = Repository(
            path=Path("/test/repo"),
            current_branch="main", 
            is_dirty=False
        )
        
        # Mock the load_repository method
        app.load_repository = AsyncMock()
        app.log = MagicMock()
        
        await app.action_refresh()
        
        app.load_repository.assert_called_once_with("/test/repo")
    
    @pytest.mark.asyncio
    async def test_help_action(self):
        """Test help action."""
        app = TuiApp()
        list(app.compose())
        
        app.log = MagicMock()
        
        await app.action_help()
        
        # Should call write_lines with help text
        app.log.write_lines.assert_called_once()
        help_lines = app.log.write_lines.call_args[0][0]
        assert "Git Patchdance - Keyboard Shortcuts" in help_lines
        assert "j, ↓    Move down" in help_lines
    
    @pytest.mark.asyncio
    async def test_run_with_repository_path(self):
        """Test running app with repository path."""
        app = TuiApp()
        
        # Mock the run_async method to avoid actually running the app
        with patch.object(app, 'run_async', new_callable=AsyncMock) as mock_run:
            await app.run("/test/repo")
            
            assert app._initial_path == "/test/repo"
            mock_run.assert_called_once()


class TestApplication:
    """Tests for the Application compatibility wrapper."""
    
    def test_application_initialization(self):
        """Test Application wrapper initialization."""
        from git_patchdance.tui.app import Application
        
        app_wrapper = Application()
        assert app_wrapper.app is not None
        assert isinstance(app_wrapper.app, TuiApp)
    
    @pytest.mark.asyncio
    async def test_application_run(self):
        """Test Application wrapper run method."""
        from git_patchdance.tui.app import Application
        
        app_wrapper = Application()
        
        # Mock the TuiApp run method
        with patch.object(app_wrapper.app, 'run', new_callable=AsyncMock) as mock_run:
            await app_wrapper.run("/test/repo")
            
            mock_run.assert_called_once_with("/test/repo")