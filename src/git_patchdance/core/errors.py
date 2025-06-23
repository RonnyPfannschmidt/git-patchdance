"""Custom exceptions for Git Patchdance."""

from pathlib import Path


class GitPatchError(Exception):
    """Base exception for Git Patchdance errors."""

    pass


class RepositoryNotFound(GitPatchError):
    """Raised when a git repository cannot be found."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Git repository not found at: {path}")


class InvalidCommitId(GitPatchError):
    """Raised when an invalid commit ID is provided."""

    def __init__(self, commit_id: str) -> None:
        self.commit_id = commit_id
        super().__init__(f"Invalid commit ID: {commit_id}")


class NoCommitsFound(GitPatchError):
    """Raised when no commits are found in the repository."""

    def __init__(self) -> None:
        super().__init__("No commits found in repository")


class ApplicationError(GitPatchError):
    """Raised when an operation application fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Application error: {message}")


class GitOperationError(GitPatchError):
    """Raised when a git operation fails."""

    def __init__(self, operation: str) -> None:
        self.operation = operation

        super().__init__(f"Git operation '{operation}' failed:")


class PatchError(GitPatchError):
    """Raised when patch operations fail."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Patch error: {message}")


class ConflictError(GitPatchError):
    """Raised when conflicts occur during operations."""

    def __init__(self, message: str, conflicts: list[str]) -> None:
        self.message = message
        self.conflicts = conflicts
        super().__init__(f"Conflicts occurred: {message}")


class ValidationError(GitPatchError):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")
