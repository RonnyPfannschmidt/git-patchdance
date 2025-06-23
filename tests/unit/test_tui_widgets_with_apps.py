"""Test TUI widgets using small Textual test apps."""

from datetime import datetime

import pytest
from textual.app import App, ComposeResult

from git_patchdance.core.models import CommitId, CommitInfo
from git_patchdance.tui.app import CommitDetails, CommitList, StatusBar


class TestCommitListApp(App):
    """Test app for CommitList widget."""

    def compose(self) -> ComposeResult:
        self.commit_list = CommitList()
        yield self.commit_list


class TestCommitDetailsApp(App):
    """Test app for CommitDetails widget."""

    def compose(self) -> ComposeResult:
        self.commit_details = CommitDetails()
        yield self.commit_details


class TestStatusBarApp(App):
    """Test app for StatusBar widget."""

    def compose(self) -> ComposeResult:
        self.status_bar = StatusBar()
        yield self.status_bar


class TestTuiWidgetsWithApps:
    """Test TUI widgets using test apps."""

    @pytest.mark.asyncio
    async def test_commit_list_widget(self):
        """Test CommitList widget in a Textual app context."""
        app = TestCommitListApp()

        async with app.run_test() as pilot:
            # Test initialization
            assert app.commit_list.border_title == "Commits"
            assert app.commit_list.commits == []

            # Test with commits
            commits = [
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

            app.commit_list.commits = commits
            await pilot.pause()

            assert len(app.commit_list.commits) == 1
            assert len(app.commit_list.children) > 0  # Should have list items

    @pytest.mark.asyncio
    async def test_commit_details_widget(self):
        """Test CommitDetails widget in a Textual app context."""
        app = TestCommitDetailsApp()

        async with app.run_test() as pilot:
            # Test initialization
            assert app.commit_details.border_title == "Commit Details"

            # Test showing commit
            commit = CommitInfo(
                id=CommitId("abc123"),
                message="Test commit message",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                parent_ids=[],
                files_changed=["test.py"],
            )

            app.commit_details.show_commit(commit)
            await pilot.pause()

            # Widget should have updated content
            content = str(app.commit_details.renderable)
            assert "abc123" in content
            assert "Test commit message" in content

    @pytest.mark.asyncio
    async def test_status_bar_widget(self):
        """Test StatusBar widget in a Textual app context."""
        app = TestStatusBarApp()

        async with app.run_test() as pilot:
            # Test initialization
            assert "Ready" in str(app.status_bar.renderable)

            # Test updating status
            app.status_bar.update("Loading...")
            await pilot.pause()

            assert "Loading..." in str(app.status_bar.renderable)

    @pytest.mark.asyncio
    async def test_commit_list_empty_state(self):
        """Test CommitList with no commits."""
        app = TestCommitListApp()

        async with app.run_test() as pilot:
            # Set empty commits
            app.commit_list.commits = []
            await pilot.pause()

            # Should show "No commits found"
            assert len(app.commit_list.children) > 0

    @pytest.mark.asyncio
    async def test_commit_list_multiple_commits(self):
        """Test CommitList with multiple commits."""
        app = TestCommitListApp()

        async with app.run_test() as pilot:
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

            app.commit_list.commits = commits
            await pilot.pause()

            assert len(app.commit_list.commits) == 3
            assert len(app.commit_list.children) == 3

    @pytest.mark.asyncio
    async def test_commit_details_with_complex_commit(self):
        """Test CommitDetails with complex commit info."""
        app = TestCommitDetailsApp()

        async with app.run_test() as pilot:
            commit = CommitInfo(
                id=CommitId("a1b2c3d4e5f6789012345678901234567890abcd"),
                message="Complex commit\n\nWith multiple lines\nand details",
                author="Complex Author",
                email="complex@example.com",
                timestamp=datetime(2023, 12, 25, 14, 30, 45),
                parent_ids=[CommitId("parent1"), CommitId("parent2")],
                files_changed=["file1.py", "file2.py", "file3.py"],
            )

            app.commit_details.show_commit(commit)
            await pilot.pause()

            content = str(app.commit_details.renderable)
            assert "a1b2c3d4e5f6789012345678901234567890abcd" in content
            assert "Complex Author" in content
            assert "Parents: 2" in content
            assert "Files: 3" in content


class TestWidgetInteractions:
    """Test widget interactions within apps."""

    @pytest.mark.asyncio
    async def test_commit_list_selection_affects_details(self):
        """Test that commit list selection updates details."""

        class InteractionTestApp(App):
            def compose(self) -> ComposeResult:
                self.commit_list = CommitList()
                self.commit_details = CommitDetails()
                yield self.commit_list
                yield self.commit_details

        app = InteractionTestApp()

        async with app.run_test() as pilot:
            commits = [
                CommitInfo(
                    id=CommitId("commit1"),
                    message="First commit",
                    author="Author 1",
                    email="author1@example.com",
                    timestamp=datetime.now(),
                    parent_ids=[],
                    files_changed=["file1.py"],
                ),
                CommitInfo(
                    id=CommitId("commit2"),
                    message="Second commit",
                    author="Author 2",
                    email="author2@example.com",
                    timestamp=datetime.now(),
                    parent_ids=[],
                    files_changed=["file2.py"],
                ),
            ]

            app.commit_list.commits = commits
            await pilot.pause()

            # Show first commit in details
            app.commit_details.show_commit(commits[0])
            await pilot.pause()

            details_content = str(app.commit_details.renderable)
            assert "First commit" in details_content
            assert "Author 1" in details_content

            # Show second commit in details
            app.commit_details.show_commit(commits[1])
            await pilot.pause()

            details_content = str(app.commit_details.renderable)
            assert "Second commit" in details_content
            assert "Author 2" in details_content
