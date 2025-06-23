"""Application events for Git Patchdance."""

from dataclasses import dataclass

from .models import CommitId


@dataclass
class LoadRepository:
    """Event to load a repository."""

    path: str | None = None


@dataclass
class RefreshCommits:
    """Event to refresh the commit list."""

    pass


@dataclass
class SelectCommit:
    """Event to select a commit."""

    commit_id: CommitId


@dataclass
class NavigateUp:
    """Event to navigate up in the commit list."""

    pass


@dataclass
class NavigateDown:
    """Event to navigate down in the commit list."""

    pass


@dataclass
class Quit:
    """Event to quit the application."""

    pass


@dataclass
class ShowHelp:
    """Event to show help."""

    pass


@dataclass
class ShowCommitDetails:
    """Event to show detailed commit information."""

    commit_id: CommitId


@dataclass
class ViewPatches:
    """Event to view patches for a commit."""

    commit_id: CommitId


@dataclass
class MovePatchEvent:
    """Event to move a patch between commits."""

    patch_id: str
    from_commit: CommitId
    to_commit: CommitId


@dataclass
class SplitCommitEvent:
    """Event to split a commit."""

    commit_id: CommitId


# Union type for all application events
AppEvent = (
    LoadRepository
    | RefreshCommits
    | SelectCommit
    | NavigateUp
    | NavigateDown
    | Quit
    | ShowHelp
    | ShowCommitDetails
    | ViewPatches
    | MovePatchEvent
    | SplitCommitEvent
)
