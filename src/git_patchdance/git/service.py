"""Git service implementation using GitPython."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, Repo
from git.objects import Commit

from ..core.errors import (
    ApplicationError,
    GitOperationError,
    InvalidCommitId,
    NoCommitsFound,
    RepositoryNotFound,
)
from ..core.models import (
    CommitGraph,
    CommitId,
    CommitInfo,
    Operation,
    OperationResult,
    Patch,
    Repository,
)
from ..core.services import GitService


class GitServiceImpl(GitService):
    """Implementation of GitService using GitPython."""

    def __init__(self):
        self._repo_cache: dict[Path, Repo] = {}

    async def open_repository(self, path: Path | None = None) -> Repository:
        """Open a git repository at the given path."""
        try:
            # Use current directory if no path provided
            repo_path = path or Path.cwd()

            # Run git operations in thread pool to avoid blocking
            repo = await asyncio.to_thread(self._discover_repository, repo_path)

            # Get repository information
            current_branch = await asyncio.to_thread(self._get_current_branch, repo)
            is_dirty = await asyncio.to_thread(self._is_repository_dirty, repo)
            head_commit = await asyncio.to_thread(self._get_head_commit, repo)

            # Get the working directory path
            work_dir = repo.working_dir
            if not work_dir:
                raise RepositoryNotFound(repo_path)

            return Repository(
                path=Path(work_dir),
                current_branch=current_branch,
                is_dirty=is_dirty,
                head_commit=head_commit,
            )

        except InvalidGitRepositoryError:
            raise RepositoryNotFound(repo_path)
        except GitCommandError as e:
            raise GitOperationError("open_repository", str(e))

    async def get_commit_graph(
        self,
        repository: Repository,
        limit: int | None = None
    ) -> CommitGraph:
        """Get the commit graph for the repository."""
        try:
            repo = await asyncio.to_thread(self._get_repo, repository.path)
            commits = await asyncio.to_thread(
                self._get_commits, repo, limit or 100
            )

            if not commits:
                raise NoCommitsFound()

            return CommitGraph(
                commits=commits,
                current_branch=repository.current_branch,
            )

        except GitCommandError as e:
            raise GitOperationError("get_commit_graph", str(e))

    async def get_commit_info(
        self,
        repository: Repository,
        commit_id: CommitId
    ) -> CommitInfo:
        """Get detailed information about a specific commit."""
        try:
            repo = await asyncio.to_thread(self._get_repo, repository.path)
            commit = await asyncio.to_thread(repo.commit, commit_id.value)
            return await asyncio.to_thread(self._convert_commit, commit)

        except Exception:
            raise InvalidCommitId(commit_id.value)

    async def get_patches(
        self,
        repository: Repository,
        commit_id: CommitId
    ) -> list[Patch]:
        """Get patches for a specific commit."""
        # TODO: Implement patch extraction from commit diffs
        return []

    async def apply_operation(
        self,
        repository: Repository,
        operation: Operation
    ) -> OperationResult:
        """Apply an operation to the repository."""
        # TODO: Implement operation application
        raise ApplicationError("Operations not yet implemented")

    async def validate_repository(self, repository: Repository) -> bool:
        """Validate that the repository is in a good state."""
        try:
            repo = await asyncio.to_thread(self._get_repo, repository.path)
            # Basic validation - check if we can access head
            await asyncio.to_thread(lambda: repo.head.commit)
            return True
        except Exception:
            return False

    def _discover_repository(self, path: Path) -> Repo:
        """Discover git repository at path."""
        if path in self._repo_cache:
            return self._repo_cache[path]

        try:
            repo = Repo(path, search_parent_directories=True)
            self._repo_cache[path] = repo
            return repo
        except InvalidGitRepositoryError:
            raise RepositoryNotFound(path)

    def _get_repo(self, path: Path) -> Repo:
        """Get repository from cache or discover it."""
        return self._discover_repository(path)

    def _get_current_branch(self, repo: Repo) -> str:
        """Get the current branch name."""
        try:
            return str(repo.active_branch.name)
        except Exception:
            # Fallback for detached HEAD
            return "HEAD"

    def _is_repository_dirty(self, repo: Repo) -> bool:
        """Check if repository has uncommitted changes."""
        return repo.is_dirty(untracked_files=True)

    def _get_head_commit(self, repo: Repo) -> CommitId | None:
        """Get the HEAD commit ID."""
        try:
            return CommitId(repo.head.commit.hexsha)
        except Exception:
            return None

    def _get_commits(self, repo: Repo, limit: int) -> list[CommitInfo]:
        """Get list of commits from repository."""
        commits = []

        try:
            # Get commits from HEAD
            for commit in repo.iter_commits(max_count=limit):
                commit_info = self._convert_commit(commit)
                commits.append(commit_info)
        except Exception as e:
            raise GitOperationError("get_commits", str(e))

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
                files_changed = [diff.a_path or diff.b_path for diff in diffs if diff.a_path or diff.b_path]
            else:
                # Initial commit - get all files
                files_changed = list(commit.stats.files.keys())
        except Exception:
            # Fallback if diff fails
            files_changed = []

        # Convert timestamp
        timestamp = datetime.fromtimestamp(
            commit.committed_date,
            tz=UTC
        )

        return CommitInfo(
            id=CommitId(commit.hexsha),
            message=commit.message,
            author=commit.author.name,
            email=commit.author.email,
            timestamp=timestamp,
            parent_ids=parent_ids,
            files_changed=files_changed,
        )
