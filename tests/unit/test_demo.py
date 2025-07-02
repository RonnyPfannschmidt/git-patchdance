"""Unit tests for demo repository creation functionality."""

from git_patchdance.demo import create_demo_repository
from git_patchdance.git.fake_repository import FakeRepository


class TestDemoRepository:
    """Test demo repository creation functionality."""

    def test_create_demo_repository_returns_fake_repository(self) -> None:
        """Test that create_demo_repository returns a FakeRepository instance."""
        repo = create_demo_repository()
        assert isinstance(repo, FakeRepository)

    def test_demo_repository_has_expected_commits(self) -> None:
        """Test that the demo repository contains the expected number of commits."""
        repo = create_demo_repository()

        # Should have 7 commits total (initial + 6 module commits)
        commit_graph = repo.get_commit_graph()
        assert len(commit_graph.commits) == 7

    def test_demo_repository_initial_commit(self) -> None:
        """Test the initial commit of the demo repository."""
        repo = create_demo_repository()
        commit_graph = repo.get_commit_graph()

        # Find the initial commit (should be the root commit)
        initial_commit = None
        for commit in commit_graph.commits:
            if not commit.parent_ids:
                initial_commit = commit
                break

        assert initial_commit is not None
        assert initial_commit.message == "Initial commit: Create submodule structure"
        assert initial_commit.author == "Demo User"
        assert "submodule/__init__.py" in initial_commit.files_changed
        assert "README.md" in initial_commit.files_changed

    def test_demo_repository_module_commits(self) -> None:
        """Test that each module commit is present with expected properties."""
        repo = create_demo_repository()
        commit_graph = repo.get_commit_graph()

        # Expected module commits
        expected_modules = [
            ("module1.py", "import line run at top"),
            ("module2.py", "validation function in middle"),
            ("module3.py", "DataProcessor class"),
            ("module4.py", "error handling at end"),
            ("module5.py", "configuration constants"),
            ("module6.py", "mixed line run patterns"),
        ]

        module_commits = []
        for commit in commit_graph.commits:
            if commit.message.startswith("Add module"):
                module_commits.append(commit)

        assert len(module_commits) == 6

        # Check that each expected module file is in the commits
        all_files = set()
        for commit in module_commits:
            all_files.update(commit.files_changed)

        for module_file, _ in expected_modules:
            expected_path = f"submodule/{module_file}"
            assert expected_path in all_files

    def test_demo_repository_has_head_commit(self) -> None:
        """Test that the demo repository has a HEAD commit."""
        repo = create_demo_repository()
        head_commit = repo.head_commit

        assert head_commit is not None

        # HEAD should point to the last commit (module6)
        commit_info = repo.get_commit_info(head_commit)
        assert "submodule/module6.py" in commit_info.files_changed

    def test_demo_repository_commit_chain(self) -> None:
        """Test that commits form a proper chain."""
        repo = create_demo_repository()
        commit_graph = repo.get_commit_graph()

        # Should have a linear history - each commit (except initial) has one parent
        initial_commits = []
        single_parent_commits = []

        for commit in commit_graph.commits:
            if not commit.parent_ids:
                initial_commits.append(commit)
            elif len(commit.parent_ids) == 1:
                single_parent_commits.append(commit)

        assert len(initial_commits) == 1  # One root commit
        assert len(single_parent_commits) == 6  # Six commits with single parent

    def test_demo_repository_file_content_patterns(self) -> None:
        """Test that demo files contain expected line run patterns."""
        repo = create_demo_repository()

        # This test would ideally check file contents, but FakeRepository
        # doesn't currently expose file contents through the protocol.
        # For now, we verify the structure is correct.

        commit_graph = repo.get_commit_graph()

        # Verify we have commits that demonstrate different line run patterns
        commit_messages = [commit.message for commit in commit_graph.commits]

        # Check for specific pattern indicators in commit messages
        pattern_indicators = [
            "line run at top",  # Beginning patterns
            "in middle",  # Middle patterns
            "at end",  # End patterns
            "configuration",  # Configuration blocks
            "mixed line run",  # Mixed patterns
        ]

        for indicator in pattern_indicators:
            assert any(
                indicator in msg for msg in commit_messages
            ), f"Missing pattern: {indicator}"

    def test_demo_repository_author_consistency(self) -> None:
        """Test that all demo commits have consistent author information."""
        repo = create_demo_repository()
        commit_graph = repo.get_commit_graph()

        for commit in commit_graph.commits:
            assert commit.author == "Demo User"
            assert commit.email == "demo@example.com"

    def test_demo_repository_submodule_structure(self) -> None:
        """Test that all files are properly organized in the submodule."""
        repo = create_demo_repository()
        commit_graph = repo.get_commit_graph()

        # Collect all files from all commits
        all_files = set()
        for commit in commit_graph.commits:
            all_files.update(commit.files_changed)

        # Check that module files are in submodule/
        module_files = [f for f in all_files if f.startswith("submodule/module")]
        assert len(module_files) == 6

        # Check that __init__.py is present
        assert "submodule/__init__.py" in all_files

        # Check that README.md is at root
        assert "README.md" in all_files
