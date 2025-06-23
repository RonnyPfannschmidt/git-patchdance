"""Shared test fixtures for Git Patchdance tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from git import Repo

from git_patchdance.core.models import CommitId, Repository


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        repo = Repo.init(repo_path)

        # Configure git user for test commits
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create initial commit
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content\n")
        repo.index.add([str(test_file)])
        initial_commit = repo.index.commit("Initial commit")

        yield {
            "path": repo_path,
            "repo": repo,
            "initial_commit": CommitId(initial_commit.hexsha),
        }


@pytest.fixture
def sample_commit_id():
    """Sample commit ID for testing."""
    return CommitId("a1b2c3d4e5f6789012345678901234567890abcd")


@pytest.fixture
def sample_repository(temp_git_repo):
    """Sample repository model for testing."""
    return Repository(
        path=temp_git_repo["path"],
        current_branch="main",
        is_dirty=False,
        head_commit=temp_git_repo["initial_commit"],
    )


@pytest.fixture
def dirty_repository(temp_git_repo):
    """Sample dirty repository for testing."""
    # Add uncommitted changes
    test_file = temp_git_repo["path"] / "test.txt"
    test_file.write_text("Modified content\n")

    return Repository(
        path=temp_git_repo["path"],
        current_branch="main",
        is_dirty=True,
        head_commit=temp_git_repo["initial_commit"],
    )
