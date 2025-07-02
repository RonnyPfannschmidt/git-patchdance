# API Reference

This document provides a comprehensive reference for Git Patchdance's public APIs. The documentation is automatically generated from the source code using mkdocstrings.

## Core Data Models

The core data models define the fundamental structures used throughout Git Patchdance for representing git repositories, commits, patches, and operations.

### Core Models

::: git_patchdance.core.models
    options:
      show_root_heading: true
      show_source: false

## Git Repository Interface

The git package provides repository abstraction and implementations.

### Repository Protocol

::: git_patchdance.git.repository
    options:
      show_root_heading: true
      show_source: false

### GitPython Implementation

::: git_patchdance.git.gitpython_repository
    options:
      show_root_heading: true
      show_source: false

### Test Implementation

::: git_patchdance.git.fake_repository
    options:
      show_root_heading: true
      show_source: false

## Terminal User Interface

### Main Application

::: git_patchdance.tui.app
    options:
      show_root_heading: true
      show_source: false

## Event System

### Application Events

::: git_patchdance.core.events
    options:
      show_root_heading: true
      show_source: false

## Error Handling

Error handling is implemented using standard Python exceptions.

### Core Errors

::: git_patchdance.core.errors
    options:
      show_root_heading: true
      show_source: false

### Exception Types

::: git_patchdance.core.exceptions
    options:
      show_root_heading: true
      show_source: false

## Command Line Interface

The CLI module provides the command-line interface and argument parsing for Git Patchdance.

::: git_patchdance.cli
    options:
      show_root_heading: true
      show_source: false

## Usage Examples

### Basic Usage

```python
from git_patchdance.cli import main

# Launch Git Patchdance TUI
main()
```

### Programmatic Usage

```python
from git_patchdance.git.gitpython_repository import GitPythonRepository
from pathlib import Path

# Create repository instance
repo = GitPythonRepository(Path("."))

# Work with git repository
if repo.is_valid():
    print(f"Repository: {repo.path}")
    print(f"Current branch: {repo.current_branch()}")
```

---

*This API reference is automatically generated from the source code using mkdocstrings. For the most up-to-date information, refer to the inline documentation in the source code.*
