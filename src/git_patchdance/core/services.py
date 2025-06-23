"""Abstract service interfaces for Git Patchdance."""

from abc import ABC, abstractmethod
from pathlib import Path

from .models import (
    CommitGraph,
    CommitId,
    CommitInfo,
    Operation,
    OperationResult,
    Patch,
    Repository,
)


class GitService(ABC):
    """Abstract interface for git operations."""

    @abstractmethod
    async def open_repository(self, path: Path | None = None) -> Repository:
        """Open a git repository at the given path."""
        pass

    @abstractmethod
    async def get_commit_graph(
        self, repository: Repository, limit: int | None = None
    ) -> CommitGraph:
        """Get the commit graph for the repository."""
        pass

    @abstractmethod
    async def get_commit_info(
        self, repository: Repository, commit_id: CommitId
    ) -> CommitInfo:
        """Get detailed information about a specific commit."""
        pass

    @abstractmethod
    async def get_patches(
        self, repository: Repository, commit_id: CommitId
    ) -> list[Patch]:
        """Get patches for a specific commit."""
        pass

    @abstractmethod
    async def apply_operation(
        self, repository: Repository, operation: Operation
    ) -> OperationResult:
        """Apply an operation to the repository."""
        pass

    @abstractmethod
    async def validate_repository(self, repository: Repository) -> bool:
        """Validate that the repository is in a good state."""
        pass
