# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Git Patchdance is an interactive terminal and GUI tool for git patch management built in Rust. It enables moving patches between commits, splitting commits, and reorganizing git history through an intuitive interface.

## Development Commands

### Build Commands
- `cargo build` - Debug build
- `cargo build --release` - Release build with optimizations
- `cargo build --features gui` - Build with GUI support (egui)
- `cargo run` - Run with default TUI interface
- `cargo run --features gui -- --gui` - Run with GUI interface

### Testing
- `cargo test` - Run all tests
- `cargo test --features gui` - Run tests with GUI features
- `cargo test --test integration` - Run integration tests only
- `cargo test test_name` - Run specific test

### Code Quality
- `cargo fmt` - Format code
- `cargo clippy` - Run linter
- `cargo clippy --features gui` - Run linter with all features
- `cargo doc --open` - Generate and open documentation

### Documentation
- `mkdocs serve` - Serve documentation locally (requires `pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin`)
- `mkdocs build` - Build static documentation

## Architecture

### Core Structure
The codebase follows a layered architecture:

- **UI Layer**: Terminal (ratatui/crossterm) and GUI (egui) interfaces
- **Application Layer**: State management and command handling
- **Domain Layer**: Patch management, git operations, and diff engine
- **Infrastructure Layer**: git2 bindings, filesystem, and logging

### Key Components

#### Patch Manager (`src/patch_manager/`)
- Core business logic for patch extraction and application
- Handles patch operations: move, split, create, merge commits
- Manages conflict detection and resolution

#### Git Service (`src/git_service/`)
- High-level git repository operations
- Repository state management and validation
- Atomic operations with rollback capability

#### Diff Engine (`src/diff_engine/`) 
- Parses and analyzes git diffs
- Extracts individual file changes and hunks
- Supports partial patch selection

### Data Models

#### Core Types
```rust
pub struct CommitId(pub git2::Oid);
pub struct PatchId(pub String);
pub struct Repository { path, git_repo, current_branch, is_dirty }
pub struct Patch { id, source_commit, target_file, hunks, mode_change }
```

#### Operations
```rust
pub enum Operation {
    MovePatch { patch_id, from_commit, to_commit, position },
    SplitCommit { source_commit, new_commits },
    CreateCommit { patches, message, position },
    MergeCommits { commit_ids, message },
}
```

## Features & Configuration

### Default Features
- `tui` - Terminal UI (enabled by default)

### Optional Features  
- `gui` - Graphical UI using egui/eframe

### Dependencies
- **Git**: git2 crate for repository operations
- **Async**: tokio runtime for async operations
- **UI**: ratatui for TUI, egui for GUI
- **CLI**: clap for command-line parsing
- **Serialization**: serde for configuration

## Testing Approach

The project uses comprehensive testing with:
- Unit tests embedded in modules (`#[cfg(test)]`)
- Integration tests in `tests/` directory
- Test utilities for creating test repositories
- Async test support with `#[tokio::test]`

### Test Repository Creation
Tests use `TestRepository` helper for creating git repositories with controlled history and commit data.

## Development Notes

- All git operations are designed to be atomic with rollback capability
- Caching strategy implemented for frequently accessed git objects
- Lazy loading for large repositories and commit histories
- Comprehensive error handling with custom error types
- Async-first design for UI responsiveness during git operations