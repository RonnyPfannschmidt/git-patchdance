# Git Patchdance

**An interactive terminal and GUI tool for advanced git patch management**

## Overview

Git Patchdance is a powerful tool that provides an intuitive interface for moving patches and partial patches between commits, creating new commits from selected changes, and performing complex git history manipulations with confidence.

## Key Features

- **Interactive Patch Management**: Move individual patches or parts of patches between commits
- **Dual Interface**: Both terminal UI (TUI) and graphical UI (GUI) options
- **Safe Operations**: Preview changes before applying, with undo functionality
- **Flexible Workflows**: Support for complex git history restructuring
- **Visual Diff Viewer**: Syntax-highlighted patch viewing and editing

## Use Cases

### Reorganizing Commits
Split large commits into focused, atomic changes by moving specific patches to new commits.

### Fixing Commit History
Move bug fixes or improvements to their logical location in the commit history.

### Cherry-Picking Enhancements
Selectively apply parts of commits across branches with fine-grained control.

### Code Review Preparation
Clean up commit history to create clear, reviewable changesets.

## Architecture

Git Patchdance is built in Rust for performance and reliability, using:

- **ratatui** for terminal user interface
- **egui** for graphical user interface  
- **git2** for robust git operations
- **tokio** for async operations

## Quick Start

```bash
# Install git-patchdance
cargo install git-patchdance

# Launch in terminal mode
git-patchdance

# Launch GUI mode
git-patchdance --gui
```

## Documentation

- [Architecture](architecture.md) - System design and components
- [UI Design](ui-design.md) - Interface specifications and workflows
- [Technical Specification](technical-spec.md) - Implementation details
- [Git Integration](git-integration.md) - Git operations and patch management
- [Development](development.md) - Building and contributing

## License

MIT License - see LICENSE file for details.