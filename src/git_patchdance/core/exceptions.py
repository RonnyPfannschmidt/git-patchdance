"""Exception classes for Git Patchdance operations.

This module defines the exception hierarchy used throughout Git Patchdance
for handling errors during git operations, patch management, and other operations.
"""

import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from .models import Conflict  # noqa: F401


class GitPatchError(Exception):
    """Base exception for all Git Patchdance operations.

    This is the root exception class that all other Git Patchdance
    exceptions inherit from. It can be used to catch any error
    from the library.
    """

    pass


class GitError(GitPatchError):
    """Git operation failed.

    Raised when an underlying git operation fails, such as repository
    access errors"""


class IoError(GitPatchError):
    """IO operation failed.

    Raised when file system operations fail, such as reading/writing
    files, accessing directories, or temporary file creation.

    Attributes:
        message: Human-readable error description
        """


class PatchError(GitPatchError):
    """Patch application failed.

    Raised when patch extraction, application, or manipulation fails.
    This includes cases where patches cannot be applied cleanly or
    when patch parsing fails.

    Attributes:
        reason: Detailed description of why the patch operation failed
    """

class ConflictError(GitPatchError):
    """Conflict detected during operation.

    Raised when conflicts are detected between patches or when
    attempting operations that would result in conflicts.

    Attributes:
        description: Human-readable description of the conflict
        conflicts: List of specific conflicts that were detected
    """

    def __init__(self, description: str, conflicts: list["Conflict"]):
        super().__init__(description)

        self.conflicts = conflicts


class RepositoryNotFound(GitPatchError):
    """Repository not found at specified path.

    Raised when trying to open a git repository at a path that
    doesn't exist or doesn't contain a valid git repository.

    Attributes:
        path: The path where the repository was expected
    """

    def __init__(self, path: Path):
        super().__init__(f"Repository not found at path: {path}")
        self.path = path


class InvalidCommitId(GitPatchError):
    """Invalid commit ID provided.

    Raised when a commit ID is malformed or doesn't exist in
    the repository.

    Attributes:
        commit_id: The invalid commit ID that was provided
    """

    def __init__(self, commit_id: str):
        super().__init__(f"Invalid commit ID: {commit_id}")
        self.commit_id = commit_id


class OperationCancelled(GitPatchError):
    """Operation cancelled by user.

    Raised when a long-running operation is cancelled by user
    request, such as through UI interaction or signal handling.
    """

    def __init__(self) -> None:
        super().__init__("Operation cancelled by user")
