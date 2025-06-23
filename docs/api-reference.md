# API Reference

This document provides a comprehensive reference for Git Patchdance's public APIs. The documentation is automatically generated from the source code using mkdocstrings.

## Core Data Models

The core data models define the fundamental structures used throughout Git Patchdance for representing git repositories, commits, patches, and operations.

### Repository Types

::: git_patchdance.core.models.Repository

::: git_patchdance.core.models.CommitId

::: git_patchdance.core.models.CommitInfo

::: git_patchdance.core.models.CommitGraph

### Patch Types

::: git_patchdance.core.models.PatchId

::: git_patchdance.core.models.Patch

::: git_patchdance.core.models.Hunk

::: git_patchdance.core.models.DiffLine

::: git_patchdance.core.models.ModeChange

### Operation Types

::: git_patchdance.core.models.InsertPosition

::: git_patchdance.core.models.MovePatch

::: git_patchdance.core.models.SplitCommit

::: git_patchdance.core.models.CreateCommit

::: git_patchdance.core.models.MergeCommits

::: git_patchdance.core.models.NewCommit

## Core Services

The core services provide high-level interfaces for git operations, patch management, and diff processing.

### Git Service

::: git_patchdance.git.service.GitService
    options:
      members:
        - open_repository
        - get_commit_graph
        - get_commit_diff
        - apply_operation
        - preview_operation

::: git_patchdance.git.service.GitServiceImpl

### Patch Manager

::: git_patchdance.patch.manager.PatchManager
    options:
      members:
        - extract_patches
        - apply_patches
        - create_commit_from_patches
        - detect_conflicts
        - apply_operation

### Diff Engine

::: git_patchdance.diff.engine.DiffEngine
    options:
      members:
        - parse_diff
        - apply_patch
        - merge_patches
        - detect_conflicts
        - extract_patches_from_commit

## Application API

### Application State

::: git_patchdance.tui.app.AppState
    options:
      members:
        - load_repository
        - select_commit
        - deselect_commit
        - queue_operation
        - get_selected_commits

### Command Handler

::: git_patchdance.tui.app.CommandHandler
    options:
      members:
        - execute_command

## Result Types

### Operation Results

::: git_patchdance.core.models.OperationResult

::: git_patchdance.core.models.OperationPreview

::: git_patchdance.core.models.Conflict

::: git_patchdance.core.models.ConflictKind

## Error Types

Error handling is implemented using standard Python exceptions with a hierarchy for different error types.

::: git_patchdance.core.exceptions.GitPatchError

::: git_patchdance.core.exceptions.GitError

::: git_patchdance.core.exceptions.PatchError

::: git_patchdance.core.exceptions.ConflictError

::: git_patchdance.core.exceptions.RepositoryNotFound

::: git_patchdance.core.exceptions.InvalidCommitId

::: git_patchdance.core.exceptions.OperationCancelled

## Command Line Interface

The CLI module provides the command-line interface and argument parsing for Git Patchdance.

::: git_patchdance.cli.main

::: git_patchdance.cli.commands

## Usage Examples

### Basic Usage

```python
import asyncio
from pathlib import Path
from git_patchdance.git.service import GitServiceImpl
from git_patchdance.patch.manager import PatchManager
from git_patchdance.core.models import MovePatch, InsertPosition

async def main():
    """Basic usage example."""
    # Initialize services
    git_service = GitServiceImpl()
    patch_manager = PatchManager(git_service)
    
    # Open repository
    repo = await git_service.open_repository(Path("."))
    
    # Get commit history
    commit_graph = await git_service.get_commit_graph(repo, limit=10)
    
    # Extract patches from a commit
    if commit_graph.commits:
        commit = commit_graph.commits[0]
        patches = await patch_manager.extract_patches(repo, commit.id)
        
        if patches and len(commit_graph.commits) > 1:
            # Move a patch to another commit
            target_commit = commit_graph.commits[1]
            operation = MovePatch(
                patch_id=patches[0].id,
                from_commit=commit.id,
                to_commit=target_commit.id,
                position=InsertPosition.AFTER
            )
            
            result = await patch_manager.apply_operation(repo, operation)
            print(f"Operation successful: {result.success}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Workflow

```python
import asyncio
from pathlib import Path
from git_patchdance.git.service import GitServiceImpl
from git_patchdance.patch.manager import PatchManager

async def advanced_patch_workflow():
    """Advanced patch workflow with filtering and conflict detection."""
    git_service = GitServiceImpl()
    patch_manager = PatchManager(git_service)
    repo = await git_service.open_repository(Path("."))
    
    # Get commit history
    commit_graph = await git_service.get_commit_graph(repo, limit=10)
    
    if len(commit_graph.commits) >= 2:
        source_commit = commit_graph.commits[0]
        target_commit = commit_graph.commits[1]
        
        # Extract patches from source commit
        all_patches = await patch_manager.extract_patches(repo, source_commit.id)
        
        # Filter patches for Python files only
        filtered_patches = [
            patch for patch in all_patches 
            if patch.target_file.suffix == ".py"
        ]
        
        if filtered_patches:
            # Check for conflicts before applying
            conflicts = await patch_manager.detect_conflicts(
                repo, filtered_patches, target_commit.id
            )
            
            if conflicts:
                print(f"Conflicts detected: {len(conflicts)} conflicts")
                for conflict in conflicts:
                    print(f"  - {conflict.description}")
                return
            
            # Apply patches if no conflicts
            result = await patch_manager.apply_patches(
                repo, filtered_patches, target_commit.id
            )
            
            print(f"Applied {len(filtered_patches)} patches to {target_commit.id.short()}")
            print(f"New commit: {result.short()}")

if __name__ == "__main__":
    asyncio.run(advanced_patch_workflow())
```

---

*This API reference is automatically generated from the source code using mkdocstrings. For the most up-to-date information, refer to the inline documentation in the source code.*