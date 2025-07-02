# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Git Patchdance is a tool to provide apis and user interfaces
for moving patch hunks or partial patch hunks between commits in a git branch



## Development

- when developing new functionality start with a test
- prefer simple abstractions
- `uv sync --dev` - Install dependencies and sync virtual environment
- `uv run pytest` - Run all tests - prefer running all tests for context
- always get feedback on code quality/linting by running `uv pre-commit run -a`


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
3. **Use fakes/standins** when external deps are to be avoided
4. **Test async operations** with proper async/await patterns

## Development Notes

- **Test-driven development**: Write tests before implementation
- **Dataclasses for state**: Use dataclasses for models, not serialization
- **Error handling**: Custom exception hierarchy for different error types
