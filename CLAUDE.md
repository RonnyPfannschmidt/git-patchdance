# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Git Patchdance is an interactive terminal tool for git patch management built in Python. It enables moving patches between commits, splitting commits, and reorganizing git history through an intuitive interface using Textual for the TUI.

## Development Commands

### Environment Setup
- `uv sync` - Install dependencies and sync virtual environment
- `uv sync --dev` - Install with development dependencies
- `uv run python -m git_patchdance` - Run the application

### Build Commands
- `uv build` - Build distribution packages
- `uv run python -m build` - Alternative build command

### Testing (Test-First Development)
- `uv run pytest` - Run all tests
- `uv run pytest tests/unit/` - Run unit tests only
- `uv run pytest tests/integration/` - Run integration tests only
- `uv run pytest -k test_name` - Run specific test
- `uv run pytest --cov` - Run tests with coverage
- `uv run pytest --cov-report=html` - Generate HTML coverage report

### Code Quality
- `uv run ruff format` - Format code
- `uv run ruff check` - Run linter
- `uv run ruff check --fix` - Run linter with auto-fix
- `uv run mypy src/` - Type checking

### Documentation
- `uv run mkdocs serve` - Serve documentation locally
- `uv run mkdocs build` - Build static documentation

## Architecture

### Core Structure
The codebase follows a layered architecture using Python:

- **UI Layer**: Textual-based terminal interface
- **Application Layer**: State management and event handling
- **Domain Layer**: Patch management, git operations, and diff engine
- **Infrastructure Layer**: GitPython bindings, filesystem, and logging

### Key Components

#### Core Package (`src/git_patchdance/core/`)
- **models.py**: Data models using dataclasses for state management
- **services.py**: Abstract service interfaces and implementations
- **errors.py**: Custom exception hierarchy
- **events.py**: Application event system
- always read the core packages for best context


#### Git Service (`src/git_patchdance/git/`)
- High-level git repository operations using GitPython
- Repository state management and validation
- Async operations for UI responsiveness

#### TUI Interface (`src/git_patchdance/tui/`)
- Textual-based terminal user interface
- Async event handling and keyboard navigation
- Responsive design with proper layout management



## Dependencies

### Core Dependencies
- **Git**: GitPython for repository operations
- **Async**: asyncio for async operations
- **UI**: Textual for modern terminal UI
- **CLI**: Click for command-line interface
- **Type Checking**: mypy for static analysis

### Development Dependencies
- **Testing**: pytest + pytest-asyncio for async testing
- **Code Quality**: ruff for formatting and linting
- **Build**: hatchling for packaging
- **Package Management**: uv for dependency management

## Testing Approach (Test-First Development)

The project uses comprehensive test-first development with:
- **Unit tests** in `tests/unit/` for individual components
- **Integration tests** in `tests/integration/` for end-to-end scenarios
- **Test utilities** for creating test repositories with controlled history
- **Async test support** with pytest-asyncio for async operations
- **Coverage reporting** to ensure comprehensive test coverage

### Test Structure
```
tests/
├── unit/
│   ├── test_models.py          # Test dataclass models
│   ├── test_git_service.py     # Test git operations
│   └── test_app_state.py       # Test application state
├── integration/
│   ├── test_full_workflow.py   # End-to-end patch operations
│   └── test_tui_interactions.py # TUI behavior testing
└── conftest.py                 # Shared test fixtures
```

### Test-First Workflow
1. **Write tests first** before implementing functionality
2. **Use fixtures** for consistent test data and repositories
3. **Mock external dependencies** (git operations, filesystem)
4. **Test async operations** with proper async/await patterns

## Development Notes

- **Test-driven development**: Write tests before implementation
- **Dataclasses for state**: Use dataclasses for models, not serialization
- **Async-first design**: UI responsiveness during git operations
- **Type hints**: Comprehensive type annotations for better tooling
- **Error handling**: Custom exception hierarchy for different error types
- **GitPython integration**: Async wrappers around GitPython operations
- **Using mocks is prohibited**

## Workflow Tips
- Don't run the terminal TUI in your own terminal, ask me to test instead
- Always write tests first, then implement the functionality
- Use `uv run pytest --cov` to check test coverage
- Run `uv run mypy src/` before committing to catch type errors