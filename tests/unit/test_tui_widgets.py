"""Tests for TUI widgets."""

import pytest
from datetime import datetime

from git_patchdance.core.models import CommitId, CommitInfo
from git_patchdance.tui.app import CommitList, CommitDetails, StatusBar


class TestCommitListWidget:
    """Tests for CommitList widget functionality."""
    
    def test_commit_list_reactive_commits(self):
        """Test commits reactive property."""
        commit_list = CommitList()
        
        # Test initial state
        assert commit_list.commits == []
        
        # Test setting commits
        commits = [
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
        
        commit_list.commits = commits
        assert commit_list.commits == commits
    
    def test_commit_list_reactive_selected_index(self):
        """Test selected_index reactive property."""
        commit_list = CommitList()
        
        # Test initial state
        assert commit_list.selected_index == 0
        
        # Test setting index
        commit_list.selected_index = 2
        assert commit_list.selected_index == 2
    
    def test_watch_commits_empty(self):
        """Test watch_commits with empty list."""
        commit_list = CommitList()
        
        # Test that method can be called without error
        commit_list.watch_commits([])
        
        # Should not crash when called with empty list
    
    def test_watch_commits_with_data(self):
        """Test watch_commits with commit data."""
        commit_list = CommitList()
        
        commits = [
            CommitInfo(
                id=CommitId("a1b2c3d4e5f6789012345678901234567890abcd"),
                message="First commit message that is quite long and should be truncated",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=["file1.txt"]
            ),
            CommitInfo(
                id=CommitId("b2c3d4e5f6789012345678901234567890abcdef"),
                message="Second commit",
                author="Another Author", 
                email="another@example.com",
                timestamp=datetime.now(),
                parent_ids=[CommitId("a1b2c3d4e5f6789012345678901234567890abcd")],
                files_changed=["file2.txt"]
            )
        ]
        
        commit_list.selected_index = 1  # Select second commit
        commit_list.commits = commits
        
        # Test that method can be called without error
        commit_list.watch_commits(commits)
        
        # Verify commits are set
        assert len(commit_list.commits) == 2
        assert commit_list.selected_index == 1
    
    def test_watch_selected_index(self):
        """Test watch_selected_index updates display."""
        commit_list = CommitList()
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
        commit_list.commits = commits
        
        # Test that method can be called without error
        commit_list.watch_selected_index(0)
        
        # Should not crash


class TestCommitDetailsWidget:
    """Tests for CommitDetails widget functionality."""
    
    def test_initialization(self):
        """Test CommitDetails initialization."""
        details = CommitDetails()
        
        assert details.border_title == "Commit Details"
    
    def test_show_commit(self):
        """Test showing commit details."""
        details = CommitDetails()
        
        commit = CommitInfo(
            id=CommitId("a1b2c3d4e5f6789012345678901234567890abcd"),
            message="Test commit message\n\nWith detailed description\nMultiple lines",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime(2023, 12, 25, 14, 30, 45),
            parent_ids=[
                CommitId("parent1"),
                CommitId("parent2")  # Merge commit
            ],
            files_changed=["file1.py", "file2.py", "file3.py"]
        )
        
        # Test that method can be called without error
        details.show_commit(commit)
        
        # Should not crash when showing commit details
    
    def test_show_commit_single_parent(self):
        """Test showing commit with single parent."""
        details = CommitDetails()
        
        commit = CommitInfo(
            id=CommitId("abc123"),
            message="Simple commit",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2023, 1, 1, 10, 0, 0),
            parent_ids=[CommitId("parent")],
            files_changed=["single_file.txt"]
        )
        
        # Test that method can be called without error
        details.show_commit(commit)
        
        # Should not crash
    
    def test_show_commit_no_parents(self):
        """Test showing initial commit (no parents)."""
        details = CommitDetails()
        
        commit = CommitInfo(
            id=CommitId("initial"),
            message="Initial commit",
            author="Author",
            email="author@example.com", 
            timestamp=datetime(2023, 1, 1, 9, 0, 0),
            parent_ids=[],  # No parents - initial commit
            files_changed=["README.md"]
        )
        
        # Test that method can be called without error
        details.show_commit(commit)
        
        # Should not crash


class TestStatusBarWidget:
    """Tests for StatusBar widget functionality."""
    
    def test_initialization(self):
        """Test StatusBar initialization."""
        status_bar = StatusBar()
        
        # Should initialize without error
        assert status_bar is not None
    
    def test_status_update(self):
        """Test updating status."""
        status_bar = StatusBar()
        
        # Test that update method can be called
        status_bar.update("Loading...")
        status_bar.update("Error occurred")
        
        # Should not crash


class TestWidgetIntegration:
    """Integration tests for widget interactions."""
    
    def test_commit_list_and_details_integration(self):
        """Test interaction between CommitList and CommitDetails."""
        commit_list = CommitList()
        commit_details = CommitDetails()
        
        # Create test commits
        commits = [
            CommitInfo(
                id=CommitId("commit1"),
                message="First commit",
                author="Author 1",
                email="author1@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=["file1.py"]
            ),
            CommitInfo(
                id=CommitId("commit2"),
                message="Second commit", 
                author="Author 2",
                email="author2@example.com",
                timestamp=datetime.now(),
                parent_ids=[CommitId("commit1")],
                files_changed=["file2.py"]
            )
        ]
        
        # Set commits in list
        commit_list.commits = commits
        
        # Test showing commits in details widget
        commit_details.show_commit(commits[0])
        commit_details.show_commit(commits[1])
        
        # Should not crash
        assert len(commit_list.commits) == 2
    
    def test_widget_update_chain(self):
        """Test chain of widget updates."""
        commit_list = CommitList()
        status_bar = StatusBar()
        
        commits = [
            CommitInfo(
                id=CommitId("abc"),
                message="Test", 
                author="Author",
                email="test@example.com",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        # Test updating widgets in sequence
        status_bar.update("Loading commits...")
        commit_list.commits = commits
        status_bar.update("Loaded 1 commit")
        
        # Should not crash
        assert len(commit_list.commits) == 1


class TestWidgetErrorHandling:
    """Tests for widget error handling."""
    
    def test_commit_list_with_invalid_commit(self):
        """Test CommitList handles invalid commit data gracefully."""
        commit_list = CommitList()
        
        # Test with commit that might have issues
        commits = [
            CommitInfo(
                id=CommitId(""),  # Empty commit ID
                message="",  # Empty message
                author="",
                email="",
                timestamp=datetime.now(),
                parent_ids=[],
                files_changed=[]
            )
        ]
        
        # Should not crash
        commit_list.commits = commits
        commit_list.watch_commits(commits)
    
    def test_commit_details_with_invalid_commit(self):
        """Test CommitDetails handles invalid commit data gracefully."""
        details = CommitDetails()
        
        commit = CommitInfo(
            id=CommitId(""),
            message="",
            author="",
            email="",
            timestamp=datetime.now(),
            parent_ids=[],
            files_changed=[]
        )
        
        # Should not crash
        details.show_commit(commit)
    
    def test_commit_list_edge_cases(self):
        """Test CommitList handles edge cases gracefully."""
        commit_list = CommitList()
        
        # Test with various edge cases
        commit_list.watch_commits([])  # Empty list
        
        # Test with changing selection index
        commit_list.selected_index = 5  # Out of bounds, but shouldn't crash
        commit_list.watch_commits([])
        
        # Should handle the cases gracefully