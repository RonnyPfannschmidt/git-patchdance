"""Core module for Git Patchdance."""

from .errors import GitPatchError
from .events import AppEvent
from .models import (
    CommitGraph,
    CommitId,
    CommitInfo,
    Conflict,
    DiffLine,
    Hunk,
    ModeChange,
    Operation,
    OperationResult,
    Patch,
    PatchId,
    Repository,
)

__all__ = [
    "GitPatchError",
    "AppEvent",
    "CommitId",
    "CommitInfo",
    "Repository",
    "PatchId",
    "Patch",
    "Hunk",
    "DiffLine",
    "ModeChange",
    "Operation",
    "OperationResult",
    "Conflict",
    "CommitGraph",
    "GitService",
]
