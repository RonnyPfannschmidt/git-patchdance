"""Custom exceptions for Git Patchdance."""


class GitPatchError(Exception):
    """Base exception for Git Patchdance errors."""


class RepositoryNotFound(GitPatchError):
    """Raised when a git repository cannot be found."""


class InvalidCommitId(GitPatchError):
    """Raised when an invalid commit ID is provided."""


class NoCommitsFound(GitPatchError):
    """Raised when no commits are found in the repository."""


class ApplicationError(GitPatchError):
    """Raised when an operation application fails."""


class GitOperationError(GitPatchError):
    """Raised when a git operation fails."""


class PatchError(GitPatchError):
    """Raised when patch operations fail."""


class ConflictError(GitPatchError):
    """Raised when conflicts occur during operations."""

    def __init__(self, message: str, conflicts: list[str]) -> None:
        self.conflicts = conflicts
        super().__init__(message)
