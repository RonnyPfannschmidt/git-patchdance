# Development Guide

This guide covers setting up the development environment, building the project, testing, and contributing to Git Patchdance.

## Prerequisites

### Required Tools

- **Python**: Version 3.11+ (install via [pyenv](https://github.com/pyenv/pyenv) or system package manager)
- **uv**: Fast Python package manager (install via [uv installer](https://docs.astral.sh/uv/getting-started/installation/))
- **Git**: Version 2.30+ for full feature compatibility

### Platform-Specific Setup

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip git
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install python3 python3-pip git
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### macOS
```bash
brew install python git
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows
```powershell
# Install Python from python.org or Microsoft Store
# Install Git from git-scm.com
# Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Project Setup

### Clone and Build

```bash
git clone https://github.com/RonnyPfannschmidt/git-patchdance.git
cd git-patchdance

# Install dependencies and sync virtual environment
uv sync

# Install with development dependencies
uv sync --group dev

# Run the application
uv run python -m git_patchdance.cli

# Run with specific repository path
uv run python -m git_patchdance.cli --path /path/to/repo
```

### Development Environment

#### VS Code Setup

Recommended VS Code extensions:
```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-python.mypy-type-checker",
        "charliermarsh.ruff"
    ]
}
```

VS Code settings (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.ruffEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

#### Python Environment Configuration

Create `.venv` directory and activate:
```bash
# uv automatically manages virtual environments
uv sync

# Activate manually if needed
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

## Documentation

### Building Documentation

#### Code Documentation
```bash
# Generate API documentation using pydoc
uv run python -m pydoc -w git_patchdance

# Generate documentation using pdoc (if available)
uv run pdoc --html git_patchdance
```

#### User Documentation
```bash
# Install MkDocs and dependencies (included in dev dependencies)
uv sync --group dev

# Serve documentation locally
uv run mkdocs serve

# Build static documentation
uv run mkdocs build

# Deploy to GitHub Pages
uv run mkdocs gh-deploy
```

### Documentation Standards

- All public APIs must have docstrings following Google style
- Use type hints throughout the codebase
- Include examples in docstrings where appropriate
- Keep documentation up-to-date with code changes

Example:
```python
async def extract_patches(
    self,
    repository: Repository,
    commit_id: CommitId,
    filter_func: Optional[Callable[[Patch], bool]] = None,
) -> list[Patch]:
    """Extract patches from a git commit.

    This function analyzes the diff between a commit and its parent(s)
    to extract individual patches that can be manipulated independently.

    Args:
        repository: The git repository containing the commit
        commit_id: The git commit ID to extract patches from
        filter_func: Optional function to filter patches

    Returns:
        A list of Patch objects representing the changes in the commit.

    Raises:
        GitPatchError: If the commit ID is invalid or git operations fail.
        RepositoryNotFound: If the repository is not accessible.

    Example:
        ```python
        from git_patchdance import GitServiceImpl, Repository

        git_service = GitServiceImpl()
        repo = await git_service.open_repository()
        patches = await git_service.extract_patches(repo, commit_id)
        print(f"Found {len(patches)} patches")
        ```
    """
    # Implementation...
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with output
uv run pytest -v

# Run specific test
uv run pytest tests/unit/test_models.py::TestCommitId::test_commit_id_creation

# Run tests for specific module
uv run pytest tests/unit/test_models.py

# Run integration tests only
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=git_patchdance --cov-report=html
```

### Test Organization

```
tests/
├── integration/           # Integration tests
│   ├── test_git_operations.py
│   ├── test_patch_management.py
│   └── test_tui_workflows.py
├── unit/                  # Unit tests
│   ├── test_models.py
│   ├── test_git_service.py
│   └── test_app_state.py
├── fixtures/              # Test data
│   ├── repos/
│   └── patches/
└── conftest.py           # Test configuration and fixtures
```

### Writing Tests

#### Unit Tests
```python
import pytest
from pathlib import Path
from git_patchdance.core.models import CommitId, CommitInfo


class TestCommitId:
    """Tests for CommitId dataclass."""

    def test_commit_id_creation(self):
        """Test creating a CommitId."""
        commit_id = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        assert commit_id.value == "a1b2c3d4e5f6789012345678901234567890abcd"

    def test_commit_id_short(self):
        """Test getting short version of commit ID."""
        commit_id = CommitId("a1b2c3d4e5f6789012345678901234567890abcd")
        assert commit_id.short() == "a1b2c3d4"


@pytest.mark.asyncio
async def test_async_operation():
    """Test async git operations."""
    # Setup
    git_service = GitServiceImpl()
    repo = await git_service.open_repository(Path("."))

    # Execute
    commit_graph = await git_service.get_commit_graph(repo, limit=10)

    # Verify
    assert len(commit_graph.commits) <= 10
    assert commit_graph.current_branch is not None
```

#### Integration Tests
```python
import pytest
from tempfile import TemporaryDirectory
from git_patchdance import GitServiceImpl, PatchManager


@pytest.mark.asyncio
async def test_full_patch_workflow():
    """Test complete patch workflow from extraction to application."""
    # Create test repository with history
    with TemporaryDirectory() as temp_dir:
        test_repo = await create_test_repo_with_commits(temp_dir, [
            ("Initial commit", {"file1.txt": "content1"}),
            ("Add feature", {"file2.txt": "content2"}),
            ("Fix bug", {"file1.txt": "fixed content1"}),
        ])

        # Initialize services
        git_service = GitServiceImpl()
        patch_manager = PatchManager(git_service)

        # Extract patches from second commit
        patches = await patch_manager.extract_patches(
            test_repo.repository, test_repo.commits[1]
        )

        # Apply patches to third commit
        result = await patch_manager.apply_patches(
            test_repo.repository, patches, test_repo.commits[2]
        )

        # Verify result
        assert result.success
        assert len(result.conflicts) == 0
```

### Test Utilities

Create test utilities in `tests/conftest.py`:

```python
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from git import Repo
from git_patchdance.core.models import CommitId, Repository


@pytest.fixture
async def temp_git_repo():
    """Create a temporary git repository for testing."""
    with TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        repo = Repo.init(repo_path)

        # Configure git user for test commits
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

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


class TestRepository:
    """Helper class for creating test repositories."""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.repo = Repo.init(temp_dir)
        self.commits: list[str] = []

        # Configure git user
        with self.repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

    def create_commit(self, message: str, files: dict[str, str]) -> str:
        """Create a commit with specified files and content."""
        # Write files
        for file_path, content in files.items():
            full_path = self.temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Stage and commit
        self.repo.index.add(list(files.keys()))
        commit = self.repo.index.commit(message)
        self.commits.append(commit.hexsha)
        return commit.hexsha
```

## Code Quality

### Linting and Formatting

```bash
# Format code
uv run ruff format src/ tests/

# Check formatting without making changes
uv run ruff format --check src/ tests/

# Run linter
uv run ruff check src/ tests/

# Run linter with auto-fix
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks using [pre-commit](https://pre-commit.com/):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

### Code Coverage

Generate code coverage reports:

```bash
# Generate coverage report
uv run pytest --cov=git_patchdance --cov-report=html

# Generate coverage for CI
uv run pytest --cov=git_patchdance --cov-report=xml

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Benchmarking

### Performance Testing

```bash
# Install benchmarking tools
uv add --group dev pytest-benchmark

# Run benchmarks
uv run pytest tests/benchmarks/ --benchmark-only

# Generate benchmark reports
uv run pytest tests/benchmarks/ --benchmark-json=benchmark.json
```

### Benchmark Structure

```python
# tests/benchmarks/test_patch_operations.py
import pytest
from git_patchdance import PatchExtractor, TestRepository


class TestPatchPerformance:
    """Performance tests for patch operations."""

    @pytest.fixture
    def large_repo(self):
        """Create a repository with many commits for benchmarking."""
        test_repo = TestRepository.with_large_history(1000)
        return test_repo

    def test_extract_patches_performance(self, benchmark, large_repo):
        """Benchmark patch extraction performance."""
        extractor = PatchExtractor(large_repo.repository)

        def extract_patches():
            return extractor.extract_patches(large_repo.commits[100])

        result = benchmark(extract_patches)
        assert len(result) > 0
```

## Contributing

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality (test-first development)
3. **Ensure all tests pass** and code is formatted
4. **Update documentation** for any API changes
5. **Submit a pull request** with clear description

### Commit Message Format

Follow conventional commits:

```
type(scope): description

Body explaining what and why vs. how

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(patch): add support for binary file patches

Implement binary patch detection and handling using GitPython's
binary diff capabilities. This enables moving binary files
between commits.

Fixes #45

test(git): add integration tests for merge conflicts

Add comprehensive test coverage for three-way merge
conflict detection and resolution workflows.

docs(api): update patch manager documentation

Clarify the behavior of patch application when conflicts
are detected and add examples for common use cases.
```

### Code Review Guidelines

#### For Contributors
- Keep PRs focused and reasonably sized
- Include tests for new functionality (test-first approach)
- Update documentation
- Respond promptly to review feedback

#### For Reviewers
- Focus on correctness, performance, and maintainability
- Provide constructive feedback
- Test the changes locally when possible
- Check for proper error handling and type hints

## Release Process

### Version Management

Git Patchdance follows semantic versioning (SemVer):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Release Checklist

1. **Update version** in `src/git_patchdance/__init__.py`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite** with coverage
4. **Build package** using uv
5. **Create git tag** and push to repository
6. **Publish to PyPI** (if applicable)
7. **Update documentation** and deploy

### Automated Releases

The project uses GitHub Actions for automated releases:

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Set up Python
        run: uv python install 3.11
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest
      - name: Build package
        run: uv build
      - name: Publish to PyPI
        run: uv publish --token ${{ secrets.PYPI_TOKEN }}
```

## Debugging

### Development Tools

```bash
# Run with debug logging
uv run python -m git_patchdance.cli --log-level DEBUG

# Profile application performance
uv run python -m cProfile -o profile.stats -m git_patchdance.cli

# Interactive debugging with ipdb
uv add --group dev ipdb
# Add `import ipdb; ipdb.set_trace()` in code
```

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Git permission errors**: Check repository permissions
3. **Type checking failures**: Update type annotations
4. **Test failures**: Run tests in isolation to identify issues

### Getting Help

- Check the [documentation](../index.md)
- Search [existing issues](https://github.com/RonnyPfannschmidt/git-patchdance/issues)
- Ask questions in discussions
- Submit bug reports with minimal reproduction cases
