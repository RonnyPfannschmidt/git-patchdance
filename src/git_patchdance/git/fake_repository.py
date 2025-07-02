"""In-memory fake implementation of GitRepository for testing."""

from datetime import UTC, datetime
from pathlib import Path

from ..core.errors import InvalidCommitId, NoCommitsFound
from ..core.models import CommitGraph, CommitId, CommitInfo, CommitRequest


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

    @property
    def path(self) -> Path:
        """Get the repository path."""
        return self._path

    @property
    def current_branch(self) -> str:
        """Get the current branch name."""
        return self._current_branch

    @property
    def is_dirty(self) -> bool:
        """Check if repository has uncommitted changes."""
        return self._is_dirty

    @property
    def head_commit(self) -> CommitId | None:
        """Get the HEAD commit ID."""
        return self._branches.get(self._current_branch)

    def get_commit_graph(
        self,
        limit: int | None = None,
        base_branch: str | None = None,
        current_branch: str | None = None,
    ) -> CommitGraph:
        """Get the commit graph for the repository."""
        if not self._commits:
            raise NoCommitsFound()

        # Use provided branch or default
        current = current_branch or self._current_branch
        base = base_branch or self._get_base_branch()

        # Get commits between base and current branch
        commits_list = self._get_commits_between_branches(base, current)

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

    def _get_base_branch(self) -> str:
        """Get the base branch (usually main or master)."""
        # Check for common base branch names in order of preference
        candidate_branches = ["main", "master", "develop", "dev"]

        # Find first candidate that exists
        for candidate in candidate_branches:
            if candidate in self._branches:
                return candidate

        # If no common base branch found, return first available branch
        branch_names = list(self._branches.keys())
        if branch_names:
            return branch_names[0]

        # Fallback
        return "main"

    def _get_commits_between_branches(
        self, base_branch: str, current_branch: str
    ) -> list[CommitInfo]:
        """Get commits between base branch and current branch."""
        # If branches are the same, return all commits
        if base_branch == current_branch:
            commits_list = list(self._commits.values())
            commits_list.sort(key=lambda c: c.timestamp, reverse=True)
            return commits_list

        # Get commit IDs for both branches
        base_commit_id = self._branches.get(base_branch)
        current_commit_id = self._branches.get(current_branch)

        if not current_commit_id:
            # Current branch doesn't exist, return all commits
            commits_list = list(self._commits.values())
            commits_list.sort(key=lambda c: c.timestamp, reverse=True)
            return commits_list

        if not base_commit_id:
            # Base branch doesn't exist, return commits from current branch
            return self._get_commits_from_branch(current_branch)

        # Find commits that are in current branch but not in base branch
        # For simplicity in fake repo, we'll use timestamp-based logic
        base_commit = self._commits[base_commit_id]

        # Get all commits newer than base commit
        newer_commits = [
            commit
            for commit in self._commits.values()
            if commit.timestamp > base_commit.timestamp
        ]

        # Sort by timestamp (newest first)
        newer_commits.sort(key=lambda c: c.timestamp, reverse=True)
        return newer_commits

    def _get_commits_from_branch(self, branch_name: str) -> list[CommitInfo]:
        """Get commits from a specific branch."""
        commit_id = self._branches.get(branch_name)
        if not commit_id:
            return []

        # For fake repo, just return all commits sorted by timestamp
        commits_list = list(self._commits.values())
        commits_list.sort(key=lambda c: c.timestamp, reverse=True)
        return commits_list

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

    def set_dirty(self, is_dirty: bool) -> None:
        """Set the dirty state of the repository (for testing)."""
        self._is_dirty = is_dirty

    def create_commit(self, request: CommitRequest) -> CommitId:
        """Create a new commit with the specified file operations."""
        # Generate a new commit ID
        import hashlib

        content = (
            f"{request.message}{request.author}{request.email}{len(self._commits)}"
        )
        commit_hash = hashlib.sha1(content.encode()).hexdigest()
        commit_id = CommitId(commit_hash)

        # Create commit info
        commit_info = CommitInfo(
            id=commit_id,
            message=request.message,
            author=request.author,
            email=request.email,
            timestamp=datetime.now(UTC),
            parent_ids=request.parent_ids,
            files_changed=request.files_changed,
        )

        # Add commit to repository
        self._commits[commit_id] = commit_info

        # Update current branch to point to new commit
        self._branches[self._current_branch] = commit_id

        return commit_id
