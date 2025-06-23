"""Unit tests for core models."""

from datetime import UTC, datetime
from pathlib import Path

from git_patchdance.core.models import (
    CommitGraph,
    CommitId,
    CommitInfo,
    DiffLine,
    Hunk,
    ModeChange,
    Patch,
    PatchId,
)


class TestCommitId:
    """Tests for CommitId dataclass."""

    def test_commit_id_creation(self):
        """Test creating a CommitId."""
        commit_id = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        assert commit_id.value == "a1b2c3d4e5f6789012345678901234567890abcd"

    def test_commit_id_short(self):
        """Test getting short version of commit ID."""
        commit_id = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        assert commit_id.short() == "a1b2c3d4"

    def test_commit_id_short_handles_short_ids(self):
        """Test short() method with already short IDs."""
        commit_id = CommitId("abc123")
        assert commit_id.short() == "abc123"

    def test_commit_id_full(self):
        """Test getting full commit ID."""
        full_sha = "a1b2c3d4e5f6789012345678901234567890abcd"
        commit_id = CommitId(full_sha)
        assert commit_id.full() == full_sha

    def test_commit_id_str_representation(self):
        """Test string representation uses short format."""
        commit_id = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        assert str(commit_id) == "a1b2c3d4"

    def test_commit_id_equality(self):
        """Test CommitId equality comparison."""
        commit_id1 = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        commit_id2 = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        commit_id3 = CommitId("different123456789012345678901234567890")

        assert commit_id1 == commit_id2
        assert commit_id1 != commit_id3


class TestCommitInfo:
    """Tests for CommitInfo dataclass."""

    def test_commit_info_creation(self):
        """Test creating a CommitInfo."""
        commit_id = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        timestamp = datetime.now(UTC)

        commit_info = CommitInfo(
            id=commit_id,
            message="Test commit message\nDetailed description",
            author="Test Author",
            email="test@example.com",
            timestamp=timestamp,
            parent_ids=[],
            files_changed=["file1.py", "file2.py"],
        )

        assert commit_info.id == commit_id
        assert commit_info.message == "Test commit message\nDetailed description"
        assert commit_info.author == "Test Author"
        assert commit_info.email == "test@example.com"
        assert commit_info.timestamp == timestamp
        assert commit_info.parent_ids == []
        assert commit_info.files_changed == ["file1.py", "file2.py"]

    def test_commit_info_summary(self):
        """Test getting commit message summary (first line)."""
        commit_info = CommitInfo(
            id=CommitId("abc123"),
            message="First line summary\nSecond line details\nThird line more",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime.now(UTC),
            parent_ids=[],
            files_changed=[],
        )

        assert commit_info.summary() == "First line summary"

    def test_commit_info_summary_empty_message(self):
        """Test summary with empty message."""
        commit_info = CommitInfo(
            id=CommitId("abc123"),
            message="",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime.now(UTC),
            parent_ids=[],
            files_changed=[],
        )

        assert commit_info.summary() == ""

    def test_commit_info_is_merge_single_parent(self):
        """Test is_merge() with single parent (not a merge)."""
        commit_info = CommitInfo(
            id=CommitId("abc123"),
            message="Regular commit",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime.now(UTC),
            parent_ids=[CommitId("parent123")],
            files_changed=[],
        )

        assert not commit_info.is_merge()

    def test_commit_info_is_merge_multiple_parents(self):
        """Test is_merge() with multiple parents (is a merge)."""
        commit_info = CommitInfo(
            id=CommitId("abc123"),
            message="Merge commit",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime.now(UTC),
            parent_ids=[CommitId("parent1"), CommitId("parent2")],
            files_changed=[],
        )

        assert commit_info.is_merge()


class TestRepository:
    """Tests for Repository dataclass."""

    def test_repository_creation(self, sample_repository):
        """Test creating a Repository."""
        assert isinstance(sample_repository.path, Path)
        assert sample_repository.current_branch == "main"
        assert sample_repository.is_dirty is False
        assert sample_repository.head_commit is not None

    def test_dirty_repository(self, dirty_repository):
        """Test dirty repository state."""
        assert dirty_repository.is_dirty is True


class TestPatchId:
    """Tests for PatchId dataclass."""

    def test_patch_id_creation(self):
        """Test creating a PatchId."""
        patch_id = PatchId("patch-123")
        assert patch_id.value == "patch-123"

    def test_patch_id_str_representation(self):
        """Test string representation."""
        patch_id = PatchId("patch-123")
        assert str(patch_id) == "patch-123"


class TestDiffLine:
    """Tests for DiffLine dataclass."""

    def test_diff_line_context(self):
        """Test creating a context diff line."""
        line = DiffLine.Context("  unchanged line")
        assert line.content == "  unchanged line"
        assert line.line_type == "context"

    def test_diff_line_addition(self):
        """Test creating an addition diff line."""
        line = DiffLine.Addition("+ added line")
        assert line.content == "+ added line"
        assert line.line_type == "addition"

    def test_diff_line_deletion(self):
        """Test creating a deletion diff line."""
        line = DiffLine.Deletion("- removed line")
        assert line.content == "- removed line"
        assert line.line_type == "deletion"


class TestHunk:
    """Tests for Hunk dataclass."""

    def test_hunk_creation(self):
        """Test creating a Hunk."""
        lines = [
            DiffLine.Context("  context line"),
            DiffLine.Deletion("- old line"),
            DiffLine.Addition("+ new line"),
        ]

        hunk = Hunk(
            old_start=10,
            old_lines=2,
            new_start=10,
            new_lines=2,
            lines=lines,
            context="function_name",
        )

        assert hunk.old_start == 10
        assert hunk.old_lines == 2
        assert hunk.new_start == 10
        assert hunk.new_lines == 2
        assert len(hunk.lines) == 3
        assert hunk.context == "function_name"


class TestModeChange:
    """Tests for ModeChange dataclass."""

    def test_new_file_mode_change(self):
        """Test creating a new file mode change."""
        mode_change = ModeChange.NewFile(mode=0o644)
        assert mode_change.mode == 0o644
        assert mode_change.change_type == "new_file"

    def test_deleted_file_mode_change(self):
        """Test creating a deleted file mode change."""
        mode_change = ModeChange.DeletedFile(mode=0o644)
        assert mode_change.mode == 0o644
        assert mode_change.change_type == "deleted_file"

    def test_mode_change(self):
        """Test creating a mode change."""
        mode_change = ModeChange.ModeChange(old_mode=0o644, new_mode=0o755)
        assert mode_change.old_mode == 0o644
        assert mode_change.new_mode == 0o755
        assert mode_change.change_type == "mode_change"


class TestPatch:
    """Tests for Patch dataclass."""

    def test_patch_creation(self):
        """Test creating a Patch."""
        patch_id = PatchId("patch-123")
        commit_id = CommitId("abc123")
        target_file = Path("src/example.py")

        hunks = [
            Hunk(
                old_start=1,
                old_lines=1,
                new_start=1,
                new_lines=1,
                lines=[DiffLine.Addition("+ new line")],
                context="",
            )
        ]

        patch = Patch(
            id=patch_id,
            source_commit=commit_id,
            target_file=target_file,
            hunks=hunks,
            mode_change=None,
        )

        assert patch.id == patch_id
        assert patch.source_commit == commit_id
        assert patch.target_file == target_file
        assert len(patch.hunks) == 1
        assert patch.mode_change is None


class TestCommitGraph:
    """Tests for CommitGraph dataclass."""

    def test_commit_graph_creation(self):
        """Test creating a CommitGraph."""
        commits = [
            CommitInfo(
                id=CommitId("commit1"),
                message="First commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(UTC),
                parent_ids=[],
                files_changed=["file1.py"],
            ),
            CommitInfo(
                id=CommitId("commit2"),
                message="Second commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(UTC),
                parent_ids=[CommitId("commit1")],
                files_changed=["file2.py"],
            ),
        ]

        commit_graph = CommitGraph(
            commits=commits,
            current_branch="main",
        )

        assert len(commit_graph.commits) == 2
        assert commit_graph.current_branch == "main"
        assert commit_graph.total_count == 2

    def test_find_commit(self):
        """Test finding a commit by ID."""
        commit1 = CommitInfo(
            id=CommitId("commit1"),
            message="First commit",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime.now(UTC),
            parent_ids=[],
            files_changed=[],
        )

        commit_graph = CommitGraph(
            commits=[commit1],
            current_branch="main",
        )

        found = commit_graph.find_commit(CommitId("commit1"))
        assert found == commit1

        not_found = commit_graph.find_commit(CommitId("nonexistent"))
        assert not_found is None

    def test_get_commit_index(self):
        """Test getting commit index by ID."""
        commits = [
            CommitInfo(
                id=CommitId("commit1"),
                message="First commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(UTC),
                parent_ids=[],
                files_changed=[],
            ),
            CommitInfo(
                id=CommitId("commit2"),
                message="Second commit",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime.now(UTC),
                parent_ids=[],
                files_changed=[],
            ),
        ]

        commit_graph = CommitGraph(
            commits=commits,
            current_branch="main",
        )

        assert commit_graph.get_commit_index(CommitId("commit1")) == 0
        assert commit_graph.get_commit_index(CommitId("commit2")) == 1
        assert commit_graph.get_commit_index(CommitId("nonexistent")) is None
