"""In-memory fake implementation of GitRepository for testing."""

from datetime import UTC, datetime
from pathlib import Path

from ..core.errors import InvalidCommitId, NoCommitsFound
from ..core.models import CommitGraph, CommitId, CommitInfo, Repository


class FakeRepository:
    """In-memory fake implementation of GitRepository protocol for testing."""

    def __init__(
        self,
        path: Path,
        commits: dict[CommitId, CommitInfo] | None = None,
        branches: dict[str, CommitId] | None = None,
        current_branch: str = "main",
        is_dirty: bool = False,
    ):
        """Initialize fake repository with test data."""
        self._path = path
        self._commits = commits or {}
        self._branches = branches or {}
        self._current_branch = current_branch
        self._is_dirty = is_dirty

        # Create head commit ID from current branch
        head_commit = self._branches.get(current_branch)

        self._repository_info = Repository(
            path=path,
            current_branch=current_branch,
            is_dirty=is_dirty,
            head_commit=head_commit,
        )

    @property
    def info(self) -> Repository:
        """Get repository information."""
        return self._repository_info

    def get_commit_graph(
        self,
        limit: int | None = None,
        base_branch: str | None = None,  # noqa: ARG002
        current_branch: str | None = None,
    ) -> CommitGraph:
        """Get the commit graph for the repository."""
        if not self._commits:
            raise NoCommitsFound()

        # Use provided branch or default
        current = current_branch or self._current_branch

        # Get commits in chronological order (newest first)
        commits_list = list(self._commits.values())
        commits_list.sort(key=lambda c: c.timestamp, reverse=True)

        # Apply limit if specified
        if limit:
            commits_list = commits_list[:limit]

        return CommitGraph(
            commits=commits_list,
            current_branch=current,
        )

    def get_commit_info(self, commit_id: CommitId) -> CommitInfo:
        """Get detailed information about a specific commit."""
        if commit_id not in self._commits:
            raise InvalidCommitId(commit_id.full)

        return self._commits[commit_id]

    @classmethod
    def create_test_repository(
        cls,
        path: Path | None = None,
        current_branch: str = "main",
        is_dirty: bool = False,
        commit_count: int = 3,
    ) -> "FakeRepository":
        """Create a fake repository with test commits."""
        repo_path = path or Path("/test/repo")

        commits = {}
        commit_ids: list[CommitId] = []

        # Create commits only if commit_count > 0
        for i in range(commit_count):
            commit_id = CommitId(f"commit{i:03d}{'0' * 37}")
            commit = CommitInfo(
                id=commit_id,
                message=f"Test commit {i}\n\nDetailed description for commit {i}",
                author="Test Author",
                email="test@example.com",
                timestamp=datetime(2024, 1, i + 1, 12, 0, 0, tzinfo=UTC),
                parent_ids=(commit_ids[-1],) if commit_ids else (),
                files_changed=[f"file{i}.py", f"test{i}.py"],
            )
            commits[commit_id] = commit
            commit_ids.append(commit_id)

        # Create branches pointing to the latest commit (if any)
        branches = {}
        if commit_ids:
            branches[current_branch] = commit_ids[-1]  # Latest commit
            if current_branch != "main":
                branches["main"] = commit_ids[-1]

        return cls(
            path=repo_path,
            commits=commits,
            branches=branches,
            current_branch=current_branch,
            is_dirty=is_dirty,
        )

    def add_commit(self, commit: CommitInfo) -> None:
        """Add a commit to the fake repository (for testing)."""
        self._commits[commit.id] = commit

        # Update current branch to point to new commit
        self._branches[self._current_branch] = commit.id

        # Update head commit
        self._repository_info = Repository(
            path=self._repository_info.path,
            current_branch=self._repository_info.current_branch,
            is_dirty=self._repository_info.is_dirty,
            head_commit=commit.id,
        )

    def add_branch(self, branch_name: str, commit_id: CommitId) -> None:
        """Add a branch pointing to a specific commit (for testing)."""
        if commit_id not in self._commits:
            raise InvalidCommitId(commit_id.full)

        self._branches[branch_name] = commit_id

    def switch_branch(self, branch_name: str) -> None:
        """Switch to a different branch (for testing)."""
        if branch_name not in self._branches:
            raise ValueError(f"Branch {branch_name} does not exist")

        self._current_branch = branch_name
        head_commit = self._branches[branch_name]

        self._repository_info = Repository(
            path=self._repository_info.path,
            current_branch=branch_name,
            is_dirty=self._repository_info.is_dirty,
            head_commit=head_commit,
        )

    def set_dirty(self, is_dirty: bool) -> None:
        """Set the dirty state of the repository (for testing)."""
        self._is_dirty = is_dirty
        self._repository_info = Repository(
            path=self._repository_info.path,
            current_branch=self._repository_info.current_branch,
            is_dirty=is_dirty,
            head_commit=self._repository_info.head_commit,
        )
