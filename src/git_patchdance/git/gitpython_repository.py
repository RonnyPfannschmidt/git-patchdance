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
from ..core.models import CommitGraph, CommitId, CommitInfo, CommitRequest


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
        base_branch: str | None = None,
        current_branch: str | None = None,
    ) -> CommitGraph:
        """Get the commit graph for the repository."""
        try:
            # Determine branches
            current = current_branch or self._get_current_branch()
            base = base_branch or self._get_base_branch()

            # Get commits between base and current branch
            commits = self._get_commits_between_branches(base, current, limit or 100)

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

    def _get_base_branch(self) -> str:
        """Get the base branch (usually main or master)."""
        # Check for common base branch names in order of preference
        candidate_branches = ["main", "master", "develop", "dev"]

        # Get all branch names
        try:
            branch_names = [ref.name for ref in self._repo.heads]

            # Find first candidate that exists
            for candidate in candidate_branches:
                if candidate in branch_names:
                    return candidate

            # If no common base branch found, return first available branch
            if branch_names:
                return branch_names[0]

            # Fallback to HEAD if no branches exist
            return "HEAD"
        except Exception:
            return "HEAD"

    def _get_commits_between_branches(
        self, base_branch: str, current_branch: str, limit: int
    ) -> list[CommitInfo]:
        """Get commits between base branch and current branch."""
        commits: list[CommitInfo] = []

        try:
            # If current branch is the same as base branch, show recent commits
            if base_branch == current_branch:
                return self._get_commits(limit)

            # Use git log syntax: base_branch..current_branch to get commits
            # that are in current_branch but not in base_branch
            commit_range = f"{base_branch}..{current_branch}"

            for commit in self._repo.iter_commits(commit_range, max_count=limit):
                commit_info = self._convert_commit(commit)
                commits.append(commit_info)

        except Exception as e:
            # Fallback to regular commit listing if range fails
            try:
                return self._get_commits(limit)
            except Exception:
                raise GitOperationError("get_commits_between_branches") from e

        return commits

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
        if isinstance(commit.message, bytes):
            message = commit.message.decode("utf-8", errors="replace")
        else:
            message = str(commit.message)

        return CommitInfo(
            id=CommitId(commit.hexsha),
            message=message,
            author=commit.author.name or "",
            email=commit.author.email or "",
            timestamp=timestamp,
            parent_ids=tuple(parent_ids) if parent_ids else (),
            files_changed=files_changed,
        )

    def create_commit(self, request: CommitRequest) -> CommitId:
        """Create a new commit with the specified file operations."""
        try:
            # Apply file operations to working directory
            for file_path, content in request.file_operations.items():
                full_path = self.path / file_path

                if content is None:
                    # File removal
                    if full_path.exists():
                        full_path.unlink()
                        # Remove from git index
                        self._repo.index.remove([str(file_path)])
                else:
                    # File creation/modification
                    # Ensure parent directories exist
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    # Write file content
                    full_path.write_text(content, encoding="utf-8")
                    # Add to git index
                    self._repo.index.add([str(file_path)])

            # Create the commit with specified author
            from git import Actor

            author = Actor(request.author, request.email)

            commit = self._repo.index.commit(
                request.message,
                author=author,
                committer=author,
                parent_commits=[
                    self._repo.commit(pid.full) for pid in request.parent_ids
                ]
                if request.parent_ids
                else None,
            )

            return CommitId(commit.hexsha)

        except Exception as e:
            raise GitOperationError("create_commit") from e
