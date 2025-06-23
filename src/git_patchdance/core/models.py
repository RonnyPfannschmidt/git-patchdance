"""Core data models for Git Patchdance using dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, NewType

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path


@dataclass
class CommitId:
    """Represents a git commit ID/SHA."""

    value: str

    def short(self) -> str:
        """Get the short version of the commit ID (first 8 characters)."""
        return self.value[:8] if len(self.value) >= 8 else self.value

    def full(self) -> str:
        """Get the full commit ID."""
        return self.value


@dataclass
class CommitInfo:
    """Information about a git commit."""

    id: CommitId
    message: str
    author: str
    email: str
    timestamp: datetime
    parent_ids: list[CommitId]
    files_changed: list[str]

    def summary(self) -> str:
        """Get the commit message summary (first line)."""
        return self.message.split("\n", 1)[0] if self.message else ""

    def is_merge(self) -> bool:
        """Check if this is a merge commit (has multiple parents)."""
        return len(self.parent_ids) > 1


@dataclass
class Repository:
    """Represents a git repository."""

    path: Path
    current_branch: str
    is_dirty: bool
    head_commit: CommitId | None


PatchId = NewType("PatchId", str)


@dataclass
class DiffLine:
    """Represents a line in a diff."""

    content: str
    line_type: str

    @classmethod
    def Context(cls, content: str) -> DiffLine:
        """Create a context line (unchanged)."""
        return cls(content=content, line_type="context")

    @classmethod
    def Addition(cls, content: str) -> DiffLine:
        """Create an addition line (added)."""
        return cls(content=content, line_type="addition")

    @classmethod
    def Deletion(cls, content: str) -> DiffLine:
        """Create a deletion line (removed)."""
        return cls(content=content, line_type="deletion")


@dataclass(frozen=True)
class LineRun:
    start: int
    lines: int


@dataclass
class Hunk:
    """Represents a hunk in a diff."""

    old: LineRun
    new: LineRun
    lines: list[DiffLine]
    context: str


@dataclass
class ModeChange:
    """Represents a file mode change."""

    change_type: str
    mode: int | None = None
    old_mode: int | None = None
    new_mode: int | None = None

    @classmethod
    def NewFile(cls, mode: int) -> ModeChange:
        """Create a new file mode change."""
        return cls(change_type="new_file", mode=mode)

    @classmethod
    def DeletedFile(cls, mode: int) -> ModeChange:
        """Create a deleted file mode change."""
        return cls(change_type="deleted_file", mode=mode)

    @classmethod
    def ModeChange(cls, old_mode: int, new_mode: int) -> ModeChange:
        """Create a mode change."""
        return cls(change_type="mode_change", old_mode=old_mode, new_mode=new_mode)


@dataclass
class Patch:
    """Represents a patch (changes to a file)."""

    id: PatchId
    source_commit: CommitId
    target_file: Path
    hunks: list[Hunk]
    mode_change: ModeChange | None


class InsertPosition(Enum):
    """Where to insert a new commit."""

    BEFORE = "before"
    AFTER = "after"
    AT_BRANCH_HEAD = "at_branch_head"


@dataclass
class NewCommit:
    """Represents a new commit to be created."""

    message: str
    patches: list[PatchId]
    position: InsertPosition


@dataclass
class MovePatch:
    """Operation to move a patch between commits."""

    patch_id: PatchId
    from_commit: CommitId
    to_commit: CommitId
    position: InsertPosition


@dataclass
class SplitCommit:
    """Operation to split a commit into multiple commits."""

    source_commit: CommitId
    new_commits: list[NewCommit]


@dataclass
class CreateCommit:
    """Operation to create a new commit."""

    patches: list[PatchId]
    message: str
    position: InsertPosition


@dataclass
class MergeCommits:
    """Operation to merge multiple commits."""

    commit_ids: list[CommitId]
    message: str


# Union type for all operations
Operation = MovePatch | SplitCommit | CreateCommit | MergeCommits


class ConflictKind(Enum):
    """Types of conflicts that can occur."""

    CONTENT_CONFLICT = "content_conflict"
    MODE_CONFLICT = "mode_conflict"
    DELETE_MODIFY_CONFLICT = "delete_modify_conflict"
    RENAME_CONFLICT = "rename_conflict"


@dataclass
class Conflict:
    """Represents a conflict during an operation."""

    id: str
    kind: ConflictKind
    file_path: Path
    description: str
    our_content: str
    their_content: str


@dataclass
class OperationResult:
    """Result of applying an operation."""

    success: bool
    new_commit_ids: list[CommitId]
    modified_commits: list[CommitId]
    conflicts: list[Conflict]
    message: str


@dataclass
class CommitGraph:
    """Represents a graph of commits."""

    commits: list[CommitInfo]
    current_branch: str
    total_count: int | None = None

    def __post_init__(self) -> None:
        """Set total_count if not provided."""
        if self.total_count is None:
            self.total_count = len(self.commits)

    def find_commit(self, commit_id: CommitId) -> CommitInfo | None:
        """Find a commit by its ID."""
        for commit in self.commits:
            if commit.id == commit_id:
                return commit
        return None

    def get_commit_index(self, commit_id: CommitId) -> int | None:
        """Get the index of a commit by its ID."""
        for i, commit in enumerate(self.commits):
            if commit.id == commit_id:
                return i
        return None
