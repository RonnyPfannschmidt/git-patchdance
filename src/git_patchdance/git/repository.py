"""Git repository interface and implementations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..core.models import CommitGraph, CommitId, CommitInfo, CommitRequest


def open_repository(path: Path | None = None) -> GitRepository:
    """Open a git repository at the given path and return a GitRepository instance."""
    from .gitpython_repository import GitPythonRepository

    return GitPythonRepository(path or Path.cwd())


class GitRepository(Protocol):
    """Protocol for git repository operations."""

    @property
    def path(self) -> Path:
        """Get the repository path."""
        ...

    @property
    def current_branch(self) -> str:
        """Get the current branch name."""
        ...

    @property
    def is_dirty(self) -> bool:
        """Check if repository has uncommitted changes."""
        ...

    @property
    def head_commit(self) -> CommitId | None:
        """Get the HEAD commit ID."""
        ...

    def get_commit_graph(
        self,
        limit: int | None = None,
        base_branch: str | None = None,
        current_branch: str | None = None,
    ) -> CommitGraph:
        """Get the commit graph for the repository.

        Args:
            limit: Maximum number of commits to fetch
            base_branch: Base branch to compare against (defaults to main/master)
            current_branch: Current branch to analyze (defaults to checked out branch)
        """
        ...

    def get_commit_info(self, commit_id: CommitId) -> CommitInfo:
        """Get detailed information about a specific commit."""
        ...

    def create_commit(self, request: CommitRequest) -> CommitId:
        """Create a new commit with the specified file operations.

        Args:
            request: CommitRequest containing commit details and file operations

        Returns:
            CommitId of the newly created commit
        """
        ...
