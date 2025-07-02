"""Unit tests for commit creation functionality."""

from pathlib import Path, PurePath

import pytest
from git import Repo

from git_patchdance.core.models import CommitId, CommitRequest
from git_patchdance.git.fake_repository import FakeRepository
from git_patchdance.git.gitpython_repository import GitPythonRepository


@pytest.fixture(
    params=[
        pytest.param("fake", id="fake_repository"),
        pytest.param("real", id="gitpython_repository"),
    ]
)
def repository(
    request: pytest.FixtureRequest, tmp_path: Path
) -> FakeRepository | GitPythonRepository:
    """Fixture providing both fake and real repository implementations."""
    if request.param == "fake":
        # Create fake repository with initial commit
        return FakeRepository.create_test_repository(commit_count=1)
    else:
        # Create real git repository in temporary directory
        git_repo = Repo.init(tmp_path)

        # Configure git user for test commits
        git_repo.config_writer().set_value("user", "name", "Test User").release()
        git_repo.config_writer().set_value(
            "user", "email", "test@example.com"
        ).release()

        # Create initial commit
        test_file = tmp_path / "initial.txt"
        test_file.write_text("Initial content\n")
        git_repo.index.add([str(test_file)])
        git_repo.index.commit("Initial commit")

        return GitPythonRepository(tmp_path)


@pytest.fixture
def repository_with_file(
    repository: FakeRepository | GitPythonRepository,
) -> FakeRepository | GitPythonRepository:
    """Repository fixture with an existing file for removal tests."""
    # Create a commit with a file that can be removed
    request = CommitRequest(
        message="Add file for removal test",
        author="Test Setup",
        email="setup@example.com",
        file_operations={PurePath("to_remove.txt"): "content to remove"},
    )
    repository.create_commit(request)
    return repository


class TestCreateCommit:
    """Test commit creation functionality across repository implementations."""

    def test_create_commit_basic(
        self, repository: FakeRepository | GitPythonRepository
    ) -> None:
        """Test basic commit creation."""
        request = CommitRequest(
            message="Test commit",
            author="Test Author",
            email="test@example.com",
            file_operations={
                PurePath("test.py"): "print('hello world')",
                PurePath("README.md"): "# Test Project",
            },
        )

        commit_id = repository.create_commit(request)

        assert isinstance(commit_id, CommitId)

        # Verify commit was added
        commit_info = repository.get_commit_info(commit_id)
        assert commit_info.message == "Test commit"
        assert commit_info.author == "Test Author"
        assert commit_info.email == "test@example.com"
        assert set(commit_info.files_changed) == {"test.py", "README.md"}

    def test_create_commit_with_file_removal(
        self, repository_with_file: FakeRepository | GitPythonRepository
    ) -> None:
        """Test commit creation with file removal."""
        request = CommitRequest(
            message="Remove and add files",
            author="Developer",
            email="dev@example.com",
            file_operations={
                PurePath("new_file.py"): "# New file",
                PurePath("to_remove.txt"): None,  # Removal
            },
        )

        commit_id = repository_with_file.create_commit(request)
        commit_info = repository_with_file.get_commit_info(commit_id)

        assert commit_info.message == "Remove and add files"
        assert "new_file.py" in commit_info.files_changed

    def test_create_commit_with_parents(
        self, repository: FakeRepository | GitPythonRepository
    ) -> None:
        """Test commit creation with parent commits."""
        # Get current HEAD as parent
        current_head = repository.head_commit
        assert current_head is not None

        request = CommitRequest(
            message="Child commit",
            author="Author",
            email="author@example.com",
            file_operations={PurePath("child.py"): "# Child file"},
            parent_ids=(current_head,),
        )

        commit_id = repository.create_commit(request)
        commit_info = repository.get_commit_info(commit_id)

        assert current_head in commit_info.parent_ids

    def test_create_commit_updates_current_branch(
        self, repository: FakeRepository | GitPythonRepository
    ) -> None:
        """Test that creating a commit updates the current branch."""
        initial_head = repository.head_commit

        request = CommitRequest(
            message="New commit",
            author="Author",
            email="author@example.com",
            file_operations={PurePath("new.py"): "# New"},
        )

        new_commit_id = repository.create_commit(request)

        # Current branch should now point to new commit
        current_head = repository.head_commit
        assert current_head == new_commit_id
        assert current_head != initial_head

    def test_create_commit_empty_file_operations(
        self, repository: FakeRepository | GitPythonRepository
    ) -> None:
        """Test commit creation with no file operations."""
        request = CommitRequest(
            message="Empty commit",
            author="Author",
            email="author@example.com",
            file_operations={},
        )

        commit_id = repository.create_commit(request)
        commit_info = repository.get_commit_info(commit_id)

        assert commit_info.message == "Empty commit"

    def test_create_commit_subdirectory_files(
        self, repository: FakeRepository | GitPythonRepository
    ) -> None:
        """Test commit creation with files in subdirectories."""
        request = CommitRequest(
            message="Add nested files",
            author="Developer",
            email="dev@example.com",
            file_operations={
                PurePath("src") / "main.py": "def main(): pass",
                PurePath("tests") / "test_main.py": "def test_main(): pass",
                PurePath("docs") / "api.md": "# API Documentation",
            },
        )

        commit_id = repository.create_commit(request)
        commit_info = repository.get_commit_info(commit_id)

        expected_files = {"src/main.py", "tests/test_main.py", "docs/api.md"}
        assert set(commit_info.files_changed) == expected_files

    def test_create_multiple_commits(
        self, repository: FakeRepository | GitPythonRepository
    ) -> None:
        """Test creating multiple commits in sequence."""
        # First commit
        request1 = CommitRequest(
            message="First commit",
            author="Dev1",
            email="dev1@example.com",
            file_operations={PurePath("file1.py"): "# File 1"},
        )
        commit1_id = repository.create_commit(request1)

        # Second commit
        request2 = CommitRequest(
            message="Second commit",
            author="Dev2",
            email="dev2@example.com",
            file_operations={PurePath("file2.py"): "# File 2"},
        )
        commit2_id = repository.create_commit(request2)

        # Verify both commits exist
        commit1_info = repository.get_commit_info(commit1_id)
        commit2_info = repository.get_commit_info(commit2_id)

        assert commit1_info.message == "First commit"
        assert commit2_info.message == "Second commit"
        assert commit1_id != commit2_id

        # HEAD should point to latest commit
        assert repository.head_commit == commit2_id


class TestCommitRequestModel:
    """Test the CommitRequest data model."""

    def test_commit_request_creation(self) -> None:
        """Test basic CommitRequest creation."""
        request = CommitRequest(
            message="Test commit message",
            author="John Doe",
            email="john@example.com",
            file_operations={
                PurePath("file1.py"): "content1",
                PurePath("file2.py"): None,
            },
        )

        assert request.message == "Test commit message"
        assert request.author == "John Doe"
        assert request.email == "john@example.com"
        assert len(request.file_operations) == 2
        assert request.parent_ids == ()

    def test_commit_request_with_parents(self) -> None:
        """Test CommitRequest with parent commits."""
        parent1 = CommitId("abc123")
        parent2 = CommitId("def456")

        request = CommitRequest(
            message="Merge commit",
            author="Author",
            email="author@example.com",
            file_operations={},
            parent_ids=(parent1, parent2),
        )

        assert request.parent_ids == (parent1, parent2)

    def test_files_changed_property(self) -> None:
        """Test the files_changed property of CommitRequest."""
        request = CommitRequest(
            message="Test",
            author="Author",
            email="author@example.com",
            file_operations={
                PurePath("src/main.py"): "code",
                PurePath("tests/test.py"): None,
                PurePath("README.md"): "docs",
            },
        )

        expected_files = {"src/main.py", "tests/test.py", "README.md"}
        assert set(request.files_changed) == expected_files

    def test_purepath_file_operations(self) -> None:
        """Test that file operations work with PurePath keys."""
        file_ops = {
            PurePath("src") / "main.py": "main code",
            PurePath("tests") / "test_main.py": "test code",
            PurePath("docs") / "README.md": None,  # removal
        }

        request = CommitRequest(
            message="Test",
            author="Author",
            email="author@example.com",
            file_operations=file_ops,
        )

        assert len(request.file_operations) == 3
        assert PurePath("src/main.py") in request.file_operations
        assert request.file_operations[PurePath("src/main.py")] == "main code"
        assert request.file_operations[PurePath("docs/README.md")] is None
