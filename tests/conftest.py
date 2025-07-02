"""Shared test fixtures for Git Patchdance tests."""

from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from git import Repo

from git_patchdance.core.models import CommitId


@pytest.fixture
def temp_git_repo() -> Generator[dict[str, Any], None, None]:
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
def sample_commit_id() -> CommitId:
    """Sample commit ID for testing."""
    return CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
