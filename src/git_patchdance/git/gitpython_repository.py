"""GitPython-based implementation of GitRepository."""

from datetime import UTC, datetime
from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, Repo
from git.objects import Commit

from ..core.errors import (
    GitOperationError,
    InvalidCommitId,
    NoCommitsFound,
    RepositoryNotFound,
)
from ..core.models import CommitGraph, CommitId, CommitInfo


class GitPythonRepository:
    """GitPython-based implementation of GitRepository protocol."""

    def __init__(self, path: Path):
        """Initialize with repository path."""
        try:
            self._repo = Repo(path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            raise RepositoryNotFound(path) from None

    @property
    def path(self) -> Path:
        """Get the repository path."""
        work_dir = self._repo.working_dir
        if not work_dir:
            raise RepositoryNotFound(Path.cwd())
        return Path(work_dir)

    @property
    def current_branch(self) -> str:
        """Get the current branch name."""
        return self._get_current_branch()

    @property
    def is_dirty(self) -> bool:
        """Check if repository has uncommitted changes."""
        return self._repo.is_dirty(untracked_files=True)

    @property
    def head_commit(self) -> CommitId | None:
        """Get the HEAD commit ID."""
        return self._get_head_commit()

    def get_commit_graph(
        self,
        limit: int | None = None,
        base_branch: str | None = None,  # noqa: ARG002
        current_branch: str | None = None,
    ) -> CommitGraph:
        """Get the commit graph for the repository."""
        try:
            # Determine branches
            current = current_branch or self._get_current_branch()

            # Get commits from current branch
            commits = self._get_commits(limit or 100)

            if not commits:
                raise NoCommitsFound()

            return CommitGraph(
                commits=commits,
                current_branch=current,
            )

        except GitCommandError as e:
            raise GitOperationError("get_commit_graph") from e

    def get_commit_info(self, commit_id: CommitId) -> CommitInfo:
        """Get detailed information about a specific commit."""
        try:
            commit = self._repo.commit(commit_id.full)
            return self._convert_commit(commit)
        except Exception as e:
            raise InvalidCommitId(commit_id.full) from e

    def _get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            return str(self._repo.active_branch.name)
        except Exception:
            # Fallback for detached HEAD
            return "HEAD"

    def _get_head_commit(self) -> CommitId | None:
        """Get the HEAD commit ID."""
        try:
            return CommitId(self._repo.head.commit.hexsha)
        except Exception:
            return None

    def _get_commits(self, limit: int) -> list[CommitInfo]:
        """Get list of commits from repository."""
        commits = []

        try:
            # Get commits from HEAD
            for commit in self._repo.iter_commits(max_count=limit):
                commit_info = self._convert_commit(commit)
                commits.append(commit_info)
        except Exception as e:
            raise GitOperationError("get_commits") from e

        return commits

    def _convert_commit(self, commit: Commit) -> CommitInfo:
        """Convert GitPython commit to CommitInfo."""
        # Get parent commit IDs
        parent_ids = [CommitId(parent.hexsha) for parent in commit.parents]

        # Get list of changed files
        files_changed = []
        try:
            if commit.parents:
                # Compare with first parent to get changed files
                diffs = commit.parents[0].diff(commit)
                files_changed = [
                    val for diff in diffs if (val := diff.a_path or diff.b_path)
                ]
            else:
                # Initial commit - get all files
                files_changed = [str(x) for x in commit.stats.files]
        except Exception:
            # Fallback if diff fails
            files_changed = []

        # Convert timestamp
        timestamp = datetime.fromtimestamp(commit.committed_date, tz=UTC)

        # Handle message encoding
        match commit.message:
            case bytes() as binary_message:
                message = binary_message.decode("utf-8", errors="replace")
            case str() as message:
                pass

        return CommitInfo(
            id=CommitId(commit.hexsha),
            message=message,
            author=commit.author.name or "",
            email=commit.author.email or "",
            timestamp=timestamp,
            parent_ids=tuple(parent_ids) if parent_ids else (),
            files_changed=files_changed,
        )
