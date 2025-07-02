"""Core data models for Git Patchdance using dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, NewType

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path, PurePath


@dataclass(frozen=True)
class CommitId:
    """Represents a git commit ID/SHA."""

    full: str

    def __str__(self) -> str:
        return self.full[:8]


@dataclass
class CommitInfo:
    """Information about a git commit."""

    id: CommitId
    message: str
    author: str
    email: str
    timestamp: datetime
    parent_ids: tuple[CommitId, ...]
    files_changed: list[str]

    def summary(self) -> str:
        """Get the commit message summary (first line)."""
        return self.message.split("\n", 1)[0]

    def is_merge(self) -> bool:
        """Check if this is a merge commit (has multiple parents)."""
        return len(self.parent_ids) > 1


PatchId = NewType("PatchId", str)


class LineType(Enum):
    """Enum representing diff line types with their 2-character prefixes."""

    ADDITION = "+ "
    DELETION = "- "
    CONTEXT = "  "


@dataclass
class DiffLine:
    """Represents a line in a diff."""

    content: str
    line_type: LineType

    @classmethod
    def from_diff_line(cls, line: str) -> DiffLine:
        """Create a DiffLine from a raw diff line string."""
        if len(line) == 0:
            return cls(content="", line_type=LineType.CONTEXT)

        if line.startswith("+ "):
            return cls(content=line[2:], line_type=LineType.ADDITION)
        elif line.startswith("- "):
            return cls(content=line[2:], line_type=LineType.DELETION)
        elif line.startswith("  "):
            return cls(content=line[2:], line_type=LineType.CONTEXT)
        else:
            raise ValueError(
                f"Invalid diff line format: {line!r}. "
                f"Must start with '+ ', '- ', or '  '"
            )

    def to_diff_line(self) -> str:
        """Convert back to raw diff line format."""
        return self.line_type.value + self.content


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
class FileCreated:
    """Represents a newly created file."""

    mode: int


@dataclass
class FileDeleted:
    """Represents a deleted file."""

    mode: int


@dataclass
class ModeChanged:
    """Represents a file mode change."""

    old_mode: int
    new_mode: int


# Union type for all mode change types
ModeChange = FileCreated | FileDeleted | ModeChanged


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


# Type alias for file content or removal (None = removal)
ContentOrRemoval = str | None


@dataclass
class CommitRequest:
    """Request to create a new commit with file operations."""

    message: str
    author: str
    email: str
    file_operations: dict[PurePath, ContentOrRemoval]
    parent_ids: tuple[CommitId, ...] = ()

    @property
    def files_changed(self) -> list[str]:
        """Get list of files that will be changed."""
        return [str(path) for path in self.file_operations]
