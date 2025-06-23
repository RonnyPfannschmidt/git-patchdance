"""Integration tests for TUI application."""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from git_patchdance.core.models import CommitId, CommitInfo, CommitGraph, Repository
from git_patchdance.core.errors import GitPatchError
from git_patchdance.tui.app import TuiApp


class TestTuiIntegration:
    """Integration tests for TUI application with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_full_application_flow(self):
        """Test complete application flow from startup to navigation."""
        # Create a test repository structure
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Mock git service
            with patch('git_patchdance.tui.app.GitServiceImpl') as mock_git_service_class:
                mock_git_service = AsyncMock()
                mock_git_service_class.return_value = mock_git_service
                
                # Setup mock repository and commits
                mock_repository = Repository(
                    path=repo_path,
                    current_branch="main",
                    is_dirty=False,
                    head_commit=CommitId("latest_commit")
                )
                
                mock_commits = [
                    CommitInfo(
                        id=CommitId("commit3"),
                        message="Third commit\n\nMost recent changes",
                        author="Developer",
                        email="dev@example.com",
                        timestamp=datetime(2023, 12, 3, 15, 0, 0),
                        parent_ids=[CommitId("commit2")],
                        files_changed=["feature.py", "tests.py"]
                    ),
                    CommitInfo(
                        id=CommitId("commit2"),
                        message="Second commit\n\nAdded new functionality",
                        author="Developer",
                        email="dev@example.com",
                        timestamp=datetime(2023, 12, 2, 14, 0, 0),
                        parent_ids=[CommitId("commit1")],
                        files_changed=["feature.py"]
                    ),
                    CommitInfo(
                        id=CommitId("commit1"),
                        message="Initial commit\n\nProject setup",
                        author="Developer",
                        email="dev@example.com",
                        timestamp=datetime(2023, 12, 1, 10, 0, 0),
                        parent_ids=[],
                        files_changed=["README.md", "setup.py"]
                    )
                ]
                
                mock_commit_graph = CommitGraph(
                    commits=mock_commits,
                    current_branch="main",
                    total_count=3
                )
                
                mock_git_service.open_repository.return_value = mock_repository
                mock_git_service.get_commit_graph.return_value = mock_commit_graph
                
                # Create and initialize app
                app = TuiApp()
                
                # Compose to create widgets
                list(app.compose())
                
                # Mock widgets to avoid actual UI rendering
                app.commit_list = MagicMock()
                app.commit_details = MagicMock()
                app.status_bar = MagicMock()
                app._log_widget = MagicMock()
                
                # Test loading repository
                await app.load_repository(str(repo_path))
                
                # Verify repository was loaded
                assert app.repository == mock_repository
                assert app.commit_graph == mock_commit_graph
                assert app.selected_index == 0
                
                # Verify widgets were updated
                app.commit_list.commits = mock_commits
                app.commit_details.show_commit.assert_called_once_with(mock_commits[0])
                
                # Test navigation
                await app.action_cursor_down()
                assert app.selected_index == 1
                
                await app.action_cursor_down() 
                assert app.selected_index == 2
                
                # Test boundary - should stay at last item
                await app.action_cursor_down()
                assert app.selected_index == 2
                
                # Test navigation up
                await app.action_cursor_up()
                assert app.selected_index == 1
                
                await app.action_cursor_up()
                assert app.selected_index == 0
                
                # Test boundary - should stay at first item
                await app.action_cursor_up()
                assert app.selected_index == 0
                
                # Test refresh
                mock_git_service.reset_mock()
                await app.action_refresh()
                
                # Should call git service again
                mock_git_service.open_repository.assert_called_once_with(str(repo_path))
                mock_git_service.get_commit_graph.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_during_load(self):
        """Test error handling during repository loading."""
        with patch('git_patchdance.tui.app.GitServiceImpl') as mock_git_service_class:
            mock_git_service = AsyncMock()
            mock_git_service_class.return_value = mock_git_service
            
            # Simulate repository not found
            mock_git_service.open_repository.side_effect = GitPatchError("Repository not found")
            
            app = TuiApp()
            list(app.compose())
            
            # Mock widgets
            app.status_bar = MagicMock()
            app._log_widget = MagicMock()
            
            # Should handle error gracefully
            with pytest.raises(GitPatchError):
                await app.load_repository("/nonexistent")
            
            # Log should be updated with error
            app._log_widget.write_line.assert_called()
            error_message = app._log_widget.write_line.call_args[0][0]
            assert "Failed to load repository" in error_message
    
    @pytest.mark.asyncio
    async def test_empty_repository_handling(self):
        """Test handling of repository with no commits."""
        with patch('git_patchdance.tui.app.GitServiceImpl') as mock_git_service_class:
            mock_git_service = AsyncMock()
            mock_git_service_class.return_value = mock_git_service
            
            # Setup empty repository
            mock_repository = Repository(
                path=Path("/empty/repo"),
                current_branch="main",
                is_dirty=False
            )
            
            mock_commit_graph = CommitGraph(
                commits=[],  # No commits
                current_branch="main",
                total_count=0
            )
            
            mock_git_service.open_repository.return_value = mock_repository
            mock_git_service.get_commit_graph.return_value = mock_commit_graph
            
            app = TuiApp()
            list(app.compose())
            
            # Mock widgets
            app.commit_list = MagicMock()
            app.commit_details = MagicMock()
            app.status_bar = MagicMock()
            
            # Load empty repository
            await app.load_repository("/empty/repo")
            
            # Should handle empty repository gracefully
            assert app.commit_graph.commits == []
            assert app.selected_index == 0
            
            # Navigation should not crash
            await app.action_cursor_down()
            await app.action_cursor_up()
            
            assert app.selected_index == 0
    
    @pytest.mark.asyncio
    async def test_single_commit_repository(self):
        """Test repository with single commit."""
        with patch('git_patchdance.tui.app.GitServiceImpl') as mock_git_service_class:
            mock_git_service = AsyncMock()
            mock_git_service_class.return_value = mock_git_service
            
            # Setup repository with single commit
            mock_repository = Repository(
                path=Path("/single/repo"),
                current_branch="main",
                is_dirty=False
            )
            
            single_commit = CommitInfo(
                id=CommitId("only_commit"),
                message="Only commit in repo",
                author="Solo Developer",
                email="solo@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=["README.md"]
            )
            
            mock_commit_graph = CommitGraph(
                commits=[single_commit],
                current_branch="main",
                total_count=1
            )
            
            mock_git_service.open_repository.return_value = mock_repository
            mock_git_service.get_commit_graph.return_value = mock_commit_graph
            
            app = TuiApp()
            list(app.compose())
            
            # Mock widgets
            app.commit_list = MagicMock()
            app.commit_details = MagicMock()
            app.status_bar = MagicMock()
            
            # Load repository
            await app.load_repository("/single/repo")
            
            # Should show single commit
            assert len(app.commit_graph.commits) == 1
            assert app.selected_index == 0
            
            # Navigation should respect boundaries
            await app.action_cursor_down()
            assert app.selected_index == 0  # Stay at 0
            
            await app.action_cursor_up()
            assert app.selected_index == 0  # Stay at 0
    
    @pytest.mark.asyncio
    async def test_help_functionality(self):
        """Test help functionality."""
        app = TuiApp()
        list(app.compose())
        
        app._log_widget = MagicMock()
        
        await app.action_help()
        
        # Should write help lines to log
        app._log_widget.write_lines.assert_called_once()
        help_lines = app._log_widget.write_lines.call_args[0][0]
        
        # Verify help content
        assert isinstance(help_lines, list)
        assert len(help_lines) > 0
        assert any("Keyboard Shortcuts" in line for line in help_lines)
        assert any("Move down" in line for line in help_lines)
        assert any("Move up" in line for line in help_lines)
        assert any("Refresh" in line for line in help_lines)
        assert any("Quit" in line for line in help_lines)
    
    @pytest.mark.asyncio  
    async def test_widget_state_consistency(self):
        """Test that widget states remain consistent during operations."""
        with patch('git_patchdance.tui.app.GitServiceImpl') as mock_git_service_class:
            mock_git_service = AsyncMock()
            mock_git_service_class.return_value = mock_git_service
            
            # Setup test data
            mock_repository = Repository(
                path=Path("/test/repo"),
                current_branch="develop",
                is_dirty=True  # Test with dirty repo
            )
            
            commits = [
                CommitInfo(
                    id=CommitId(f"commit{i}"),
                    message=f"Commit {i}",
                    author="Test Author",
                    email="test@example.com",
                    timestamp=datetime.now(),
                    parent_ids=[CommitId(f"commit{i-1}")] if i > 0 else [],
                    files_changed=[f"file{i}.py"]
                )
                for i in range(5)  # 5 commits
            ]
            
            mock_commit_graph = CommitGraph(
                commits=commits,
                current_branch="develop",
                total_count=5
            )
            
            mock_git_service.open_repository.return_value = mock_repository
            mock_git_service.get_commit_graph.return_value = mock_commit_graph
            
            app = TuiApp()
            list(app.compose())
            
            # Mock widgets but track their state
            app.commit_list = MagicMock()
            app.commit_details = MagicMock()
            app.status_bar = MagicMock()
            
            # Load repository
            await app.load_repository("/test/repo")
            
            # Verify initial state
            assert app.repository.current_branch == "develop"
            assert app.repository.is_dirty is True
            assert len(app.commit_graph.commits) == 5
            assert app.selected_index == 0
            
            # Navigate through commits and verify state consistency
            for i in range(4):  # Navigate to each commit
                await app.action_cursor_down()
                assert app.selected_index == i + 1
                
                # Verify commit details are updated for each navigation
                expected_commit = commits[i + 1]
                app.commit_details.show_commit.assert_called_with(expected_commit)
            
            # Navigate back up
            for i in range(4, 0, -1):
                await app.action_cursor_up()
                assert app.selected_index == i - 1
                
                expected_commit = commits[i - 1]
                app.commit_details.show_commit.assert_called_with(expected_commit)
    
    @pytest.mark.asyncio
    async def test_refresh_with_updated_repository(self):
        """Test refresh when repository has been updated externally."""
        with patch('git_patchdance.tui.app.GitServiceImpl') as mock_git_service_class:
            mock_git_service = AsyncMock()
            mock_git_service_class.return_value = mock_git_service
            
            # Initial repository state
            initial_repository = Repository(
                path=Path("/test/repo"),
                current_branch="main", 
                is_dirty=False
            )
            
            initial_commits = [
                CommitInfo(
                    id=CommitId("commit1"),
                    message="First commit",
                    author="Author",
                    email="author@example.com",
                    timestamp=datetime.now(),
                    parent_ids=[],
                    files_changed=["file1.py"]
                )
            ]
            
            initial_commit_graph = CommitGraph(
                commits=initial_commits,
                current_branch="main",
                total_count=1
            )
            
            # Updated repository state (after external changes)
            updated_commits = initial_commits + [
                CommitInfo(
                    id=CommitId("commit2"),
                    message="New commit",
                    author="Author",
                    email="author@example.com", 
                    timestamp=datetime.now(),
                    parent_ids=[CommitId("commit1")],
                    files_changed=["file2.py"]
                )
            ]
            
            updated_commit_graph = CommitGraph(
                commits=updated_commits,
                current_branch="main",
                total_count=2
            )
            
            # First call returns initial state
            mock_git_service.open_repository.return_value = initial_repository
            mock_git_service.get_commit_graph.return_value = initial_commit_graph
            
            app = TuiApp()
            list(app.compose())
            
            # Mock widgets
            app.commit_list = MagicMock()
            app.commit_details = MagicMock()
            app.status_bar = MagicMock()
            app._log_widget = MagicMock()
            
            # Initial load
            await app.load_repository("/test/repo")
            assert len(app.commit_graph.commits) == 1
            
            # Setup for refresh - return updated state
            mock_git_service.get_commit_graph.return_value = updated_commit_graph
            
            # Refresh
            await app.action_refresh()
            
            # Should have new commit
            assert len(app.commit_graph.commits) == 2
            
            # Log should indicate refresh happened
            app._log_widget.write_line.assert_called_with("Repository refreshed")