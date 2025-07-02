# Technical Specification

This document provides detailed implementation specifications for Git Patchdance, covering API design, data structures, algorithms, and technical implementation details.

## Core Data Structures

### Repository Model

```python
@dataclass
class Repository:
    path: Path
    current_branch: str
    is_dirty: bool
    head_commit: Optional[CommitId]

@dataclass
class CommitId:
    value: str

@dataclass
class CommitInfo:
    id: CommitId
    message: str
    author: str
    email: str
    timestamp: datetime
    parent_ids: list[CommitId]
    files_changed: list[str]

@dataclass
class CommitGraph:
    commits: list[CommitInfo]
    current_branch: str
    total_count: Optional[int] = None
```

### Patch Model

```python
@dataclass
class PatchId:
    value: str

@dataclass
class Patch:
    id: PatchId
    source_commit: CommitId
    target_file: Path
    hunks: list[Hunk]
    mode_change: Optional[ModeChange]

@dataclass
class Hunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[DiffLine]
    context: str

@dataclass
class DiffLine:
    content: str
    line_type: str

    @classmethod
    def Context(cls, content: str) -> 'DiffLine':
        return cls(content=content, line_type="context")

    @classmethod
    def Addition(cls, content: str) -> 'DiffLine':
        return cls(content=content, line_type="addition")

    @classmethod
    def Deletion(cls, content: str) -> 'DiffLine':
        return cls(content=content, line_type="deletion")

@dataclass
class ModeChange:
    change_type: str
    mode: Optional[int] = None
    old_mode: Optional[int] = None
    new_mode: Optional[int] = None

    @classmethod
    def NewFile(cls, mode: int) -> 'ModeChange':
        return cls(change_type="new_file", mode=mode)

    @classmethod
    def DeletedFile(cls, mode: int) -> 'ModeChange':
        return cls(change_type="deleted_file", mode=mode)

    @classmethod
    def ModeChange(cls, old_mode: int, new_mode: int) -> 'ModeChange':
        return cls(change_type="mode_change", old_mode=old_mode, new_mode=new_mode)
```

### Operation Model

```python
class InsertPosition(Enum):
    BEFORE = "before"
    AFTER = "after"
    AT_BRANCH_HEAD = "at_branch_head"

@dataclass
class MovePatch:
    patch_id: PatchId
    from_commit: CommitId
    to_commit: CommitId
    position: InsertPosition

@dataclass
class SplitCommit:
    source_commit: CommitId
    new_commits: list['NewCommit']

@dataclass
class CreateCommit:
    patches: list[PatchId]
    message: str
    position: InsertPosition

@dataclass
class MergeCommits:
    commit_ids: list[CommitId]
    message: str

@dataclass
class NewCommit:
    message: str
    patches: list[PatchId]
    position: InsertPosition

# Union type for all operations
Operation = Union[MovePatch, SplitCommit, CreateCommit, MergeCommits]
```

## API Design

### Core Services

#### GitService

```python
class GitService(ABC):
    """Abstract interface for git operations."""

    @abstractmethod
    async def open_repository(self, path: Optional[Path] = None) -> Repository:
        """Open a git repository at the given path."""
        pass

    @abstractmethod
    async def get_commit_graph(self, repo: Repository, limit: Optional[int] = None) -> CommitGraph:
        """Get the commit graph for the repository."""
        pass

    @abstractmethod
    async def get_commit_diff(self, repo: Repository, commit_id: CommitId) -> list[Patch]:
        """Get the diff for a specific commit."""
        pass

    @abstractmethod
    async def apply_operation(self, repo: Repository, operation: Operation) -> OperationResult:
        """Apply an operation to the repository."""
        pass

    @abstractmethod
    async def preview_operation(self, repo: Repository, operation: Operation) -> OperationPreview:
        """Preview the effects of an operation."""
        pass

class GitServiceImpl(GitService):
    """Implementation of GitService using GitPython."""

    def __init__(self):
        self._repo_cache: dict[Path, Repository] = {}

@dataclass
class OperationResult:
    success: bool
    new_commit_ids: list[CommitId]
    modified_commits: list[CommitId]
    conflicts: list[Conflict]
    message: str

@dataclass
class OperationPreview:
    changes: list[PreviewChange]
    potential_conflicts: list[Conflict]
    affected_commits: list[CommitId]
```

#### PatchManager

```python
class PatchManager:
    """High-level interface for patch manipulation."""

    def __init__(self, git_service: GitService):
        self.git_service = git_service
        self.diff_engine = DiffEngine()

    async def extract_patches(self, repo: Repository, commit_id: CommitId) -> list[Patch]:
        """Extract patches from a commit."""
        pass

    async def apply_patches(self, repo: Repository, patches: list[Patch], target: CommitId) -> CommitId:
        """Apply patches to a target commit."""
        pass

    async def create_commit_from_patches(self, repo: Repository, patches: list[Patch], message: str) -> CommitId:
        """Create a new commit from a collection of patches."""
        pass

    async def detect_conflicts(self, repo: Repository, patches: list[Patch], target: CommitId) -> list[Conflict]:
        """Detect potential conflicts when applying patches."""
        pass
```

#### DiffEngine

```python
class ConflictKind(Enum):
    CONTENT_CONFLICT = "content_conflict"
    MODE_CONFLICT = "mode_conflict"
    DELETE_MODIFY_CONFLICT = "delete_modify_conflict"
    RENAME_CONFLICT = "rename_conflict"

@dataclass
class Conflict:
    id: str
    kind: ConflictKind
    file_path: Path
    description: str
    our_content: str
    their_content: str

class DiffEngine:
    """Low-level diff parsing and manipulation."""

    def parse_diff(self, diff_text: str) -> list[Patch]:
        """Parse a git diff into patch objects."""
        pass

    def apply_patch(self, original: str, patch: Patch) -> str:
        """Apply a patch to file content."""
        pass

    def merge_patches(self, patches: list[Patch]) -> Patch:
        """Merge multiple patches affecting the same file."""
        pass

    def detect_conflicts(self, patch1: Patch, patch2: Patch) -> list[Conflict]:
        """Detect conflicts between patches."""
        pass

    def resolve_conflict(self, conflict: Conflict, resolution: ConflictResolution) -> Patch:
        """Resolve a conflict with the given resolution."""
        pass
```

## Algorithm Specifications

### Patch Extraction Algorithm

```python
class DiffEngine:
    async def extract_patches_from_commit(self, repo: Repository, commit_id: CommitId) -> list[Patch]:
        """Extract patches from a git commit."""
        patches = []

        # Get GitPython repository and commit
        git_repo = Repo(repo.path)
        commit = git_repo.commit(commit_id.value)

        # Get parent commit (handle initial commit case)
        parents = commit.parents
        parent = parents[0] if parents else None

        # Generate diff between commit and parent
        if parent:
            diffs = parent.diff(commit, create_patch=True)
        else:
            # Initial commit - diff against empty tree
            diffs = commit.diff(git_repo.commit('4b825dc642cb6eb9a060e54bf8d69288fbee4904'), create_patch=True)

        # Process each diff (file change)
        for diff_item in diffs:
            patch = await self._process_diff_item(diff_item, commit_id)
            if patch:
                patches.append(patch)

        return patches

    async def _process_diff_item(self, diff_item, source_commit: CommitId) -> Optional[Patch]:
        """Process a single diff item into a Patch."""
        # Extract file path
        file_path = Path(diff_item.a_path or diff_item.b_path)

        # Generate patch ID
        patch_id = PatchId(f"{source_commit.short()}:{file_path}")

        # Parse hunks from diff
        hunks = self._parse_hunks(diff_item.diff.decode('utf-8'))

        # Detect mode changes
        mode_change = self._detect_mode_change(diff_item)

        return Patch(
            id=patch_id,
            source_commit=source_commit,
            target_file=file_path,
            hunks=hunks,
            mode_change=mode_change,
        )
```

### Patch Application Algorithm

```python
class PatchManager:
    async def apply_patch_to_commit(self, repo: Repository, patch: Patch, target_commit: CommitId) -> CommitId:
        """Apply a patch to a target commit."""
        # 1. Get GitPython repository
        git_repo = Repo(repo.path)
        target_commit_obj = git_repo.commit(target_commit.value)

        # 2. Create temporary workspace
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Checkout target commit to temp directory
            await self._checkout_commit_to_temp(git_repo, target_commit_obj, temp_path)

            # 3. Apply patch to files in temp directory
            await self._apply_patch_to_files(temp_path, patch)

            # 4. Stage changes in a new index
            temp_index_path = temp_path / '.git' / 'temp_index'

            # Create new commit with changes
            new_commit_id = await self._create_commit_from_temp(
                git_repo, temp_path, target_commit_obj,
                f"Apply patch from {patch.source_commit.short()}"
            )

        return new_commit_id

    async def _apply_patch_to_files(self, temp_path: Path, patch: Patch) -> None:
        """Apply patch changes to files in temporary directory."""
        target_file = temp_path / patch.target_file

        # Read current file content
        if target_file.exists():
            original_content = target_file.read_text()
        else:
            original_content = ""

        # Apply hunks to content
        modified_content = await self._apply_hunks_to_content(original_content, patch.hunks)

        # Write modified content
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(modified_content)

        # Apply mode changes if any
        if patch.mode_change:
            await self._apply_mode_change(target_file, patch.mode_change)
```

### Conflict Detection Algorithm

```python
class DiffEngine:
    def detect_patch_conflicts(self, patches: list[Patch]) -> list[Conflict]:
        """Detect conflicts between multiple patches."""
        conflicts = []

        # Build line-level change map
        line_changes: dict[tuple[Path, int], list[Patch]] = defaultdict(list)

        for patch in patches:
            for hunk in patch.hunks:
                # Map each affected line to the patches that modify it
                for line_no in range(hunk.old_start, hunk.old_start + hunk.old_lines):
                    line_changes[(patch.target_file, line_no)].append(patch)

        # Detect conflicts where multiple patches modify same lines
        for (file_path, line_no), modifying_patches in line_changes.items():
            if len(modifying_patches) > 1:
                conflicts.append(Conflict(
                    id=f"{file_path}:{line_no}",
                    kind=ConflictKind.CONTENT_CONFLICT,
                    file_path=file_path,
                    description=f"Line {line_no} modified by {len(modifying_patches)} patches",
                    our_content=self._extract_patch_content(modifying_patches[0]),
                    their_content=self._extract_patch_content(modifying_patches[1]),
                ))

        return conflicts

    def _extract_patch_content(self, patch: Patch) -> str:
        """Extract content from a patch for conflict resolution."""
        content_lines = []
        for hunk in patch.hunks:
            for line in hunk.lines:
                if line.line_type in ("addition", "context"):
                    content_lines.append(line.content)
        return "\n".join(content_lines)
```

## Caching Strategy

### GitCache Implementation

```python
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass, field
from functools import lru_cache

@dataclass
class GitCache:
    """LRU cache for git objects to improve performance."""

    capacity: int = 1000
    commits: Dict[str, CommitInfo] = field(default_factory=dict)
    patches: Dict[str, List[Patch]] = field(default_factory=dict)
    diffs: Dict[Tuple[str, str], str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize LRU cache functionality."""
        # Using functools.lru_cache for method-level caching
        self._get_commit_cached = lru_cache(maxsize=self.capacity)(self._get_commit_impl)
        self._get_patches_cached = lru_cache(maxsize=self.capacity)(self._get_patches_impl)

    def get_commit(self, commit_id: CommitId) -> Optional[CommitInfo]:
        """Get cached commit info."""
        return self._get_commit_cached(commit_id.value)

    def cache_commit(self, commit_id: CommitId, info: CommitInfo) -> None:
        """Cache commit info."""
        self.commits[commit_id.value] = info

    def get_patches(self, commit_id: CommitId) -> Optional[List[Patch]]:
        """Get cached patches for commit."""
        return self._get_patches_cached(commit_id.value)

    def cache_patches(self, commit_id: CommitId, patches: List[Patch]) -> None:
        """Cache patches for commit."""
        self.patches[commit_id.value] = patches

    def invalidate_commit(self, commit_id: CommitId) -> None:
        """Invalidate cached data for a commit."""
        commit_key = commit_id.value

        # Clear from dictionaries
        self.commits.pop(commit_key, None)
        self.patches.pop(commit_key, None)

        # Clear diff cache entries involving this commit
        keys_to_remove = [
            key for key in self.diffs.keys()
            if commit_key in key
        ]
        for key in keys_to_remove:
            self.diffs.pop(key, None)

        # Clear LRU caches
        self._get_commit_cached.cache_clear()
        self._get_patches_cached.cache_clear()

    def _get_commit_impl(self, commit_id: str) -> Optional[CommitInfo]:
        """Implementation for commit retrieval."""
        return self.commits.get(commit_id)

    def _get_patches_impl(self, commit_id: str) -> Optional[List[Patch]]:
        """Implementation for patches retrieval."""
        return self.patches.get(commit_id)
```

## Error Handling

### Error Types

```python
from typing import List, Optional
from pathlib import Path

class GitPatchError(Exception):
    """Base exception for all Git Patchdance operations."""
    pass

class GitError(GitPatchError):
    """Git operation failed."""

    def __init__(self, message: str, git_error: Optional[Exception] = None):
        super().__init__(f"Git operation failed: {message}")
        self.git_error = git_error

class IoError(GitPatchError):
    """IO operation failed."""

    def __init__(self, message: str, io_error: Optional[Exception] = None):
        super().__init__(f"IO operation failed: {message}")
        self.io_error = io_error

class PatchError(GitPatchError):
    """Patch application failed."""

    def __init__(self, reason: str):
        super().__init__(f"Patch application failed: {reason}")
        self.reason = reason

class ConflictError(GitPatchError):
    """Conflict detected during operation."""

    def __init__(self, description: str, conflicts: List['Conflict']):
        super().__init__(f"Conflict detected: {description}")
        self.description = description
        self.conflicts = conflicts

class RepositoryNotFound(GitPatchError):
    """Repository not found at specified path."""

    def __init__(self, path: Path):
        super().__init__(f"Repository not found at path: {path}")
        self.path = path

class InvalidCommitId(GitPatchError):
    """Invalid commit ID provided."""

    def __init__(self, commit_id: str):
        super().__init__(f"Invalid commit ID: {commit_id}")
        self.commit_id = commit_id

class OperationCancelled(GitPatchError):
    """Operation cancelled by user."""

    def __init__(self):
        super().__init__("Operation cancelled by user")

# Type alias for Result pattern
from typing import Union, TypeVar

T = TypeVar('T')
Result = Union[T, GitPatchError]
```

### Error Recovery

```python
from typing import Dict, Any
import asyncio
import shutil
from pathlib import Path

class PatchManager:
    async def recover_from_failed_operation(
        self,
        repo: Repository,
        operation_id: str
    ) -> None:
        """Recover from a failed operation by rolling back changes."""
        try:
            # 1. Load operation state from backup
            backup_state = await self.load_operation_backup(operation_id)

            # 2. Rollback git changes
            await self.rollback_git_changes(repo, backup_state)

            # 3. Clean up temporary files
            await self.cleanup_temp_files(backup_state)

            # 4. Reset application state
            await self.reset_app_state(backup_state)

        except Exception as e:
            raise GitError(f"Failed to recover from operation {operation_id}") from e

    async def load_operation_backup(self, operation_id: str) -> Dict[str, Any]:
        """Load operation backup state."""
        backup_file = Path(f".git/patchdance/backups/{operation_id}.json")
        if not backup_file.exists():
            raise IoError(f"Backup file not found: {backup_file}")

        import json
        with backup_file.open() as f:
            return json.load(f)

    async def rollback_git_changes(
        self,
        repo: Repository,
        backup_state: Dict[str, Any]
    ) -> None:
        """Rollback git repository changes."""
        from git import Repo

        git_repo = Repo(repo.path)

        # Reset to original HEAD if specified
        if 'original_head' in backup_state:
            git_repo.git.reset('--hard', backup_state['original_head'])

        # Restore refs if they were modified
        if 'original_refs' in backup_state:
            for ref_name, ref_value in backup_state['original_refs'].items():
                git_repo.refs[ref_name].set_commit(ref_value)

    async def cleanup_temp_files(self, backup_state: Dict[str, Any]) -> None:
        """Clean up temporary files created during operation."""
        if 'temp_files' in backup_state:
            for temp_file in backup_state['temp_files']:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    if temp_path.is_dir():
                        shutil.rmtree(temp_path)
                    else:
                        temp_path.unlink()

    async def reset_app_state(self, backup_state: Dict[str, Any]) -> None:
        """Reset application state to pre-operation state."""
        # This would reset any application-level state
        # that was modified during the failed operation
        pass
```

## Performance Optimizations

### Lazy Loading Strategy

```python
from typing import Set, Dict, Deque, Optional
from collections import deque
import asyncio

@dataclass
class LazyCommitGraph:
    """Lazy-loading commit graph for large repositories."""

    repo: Repository
    loaded_commits: Set[str] = field(default_factory=set)
    commit_cache: Dict[str, CommitInfo] = field(default_factory=dict)
    loading_queue: Deque[str] = field(default_factory=deque)
    batch_size: int = 50

    async def load_commit_range(
        self,
        start: CommitId,
        count: int
    ) -> List[CommitInfo]:
        """Load a range of commits starting from the given commit."""
        commits = []
        current = start.value

        # Load commits in batches for better performance
        for i in range(0, count, self.batch_size):
            batch_count = min(self.batch_size, count - i)
            batch_commits = await self._load_commit_batch(current, batch_count)
            commits.extend(batch_commits)

            if batch_commits:
                # Move to next commit after the batch
                last_commit = batch_commits[-1]
                if last_commit.parent_ids:
                    current = last_commit.parent_ids[0].value
                else:
                    break
            else:
                break

        return commits[:count]

    async def _load_commit_batch(
        self,
        start: str,
        count: int
    ) -> List[CommitInfo]:
        """Load a batch of commits."""
        commits = []
        current = start

        for _ in range(count):
            if current not in self.loaded_commits:
                info = await self.load_commit_info(current)
                if info:
                    self.commit_cache[current] = info
                    self.loaded_commits.add(current)
                    commits.append(info)
                else:
                    break
            else:
                cached_info = self.commit_cache.get(current)
                if cached_info:
                    commits.append(cached_info)

            # Move to next commit (first parent)
            current_info = self.commit_cache.get(current)
            if current_info and current_info.parent_ids:
                current = current_info.parent_ids[0].value
            else:
                break

        return commits

    async def load_commit_info(self, commit_id: str) -> Optional[CommitInfo]:
        """Load commit information from git repository."""
        try:
            from git import Repo
            git_repo = Repo(self.repo.path)
            commit = git_repo.commit(commit_id)

            return CommitInfo(
                id=CommitId(commit.hexsha),
                message=commit.message.strip(),
                author=commit.author.name,
                email=commit.author.email,
                timestamp=commit.committed_datetime,
                parent_ids=[CommitId(parent.hexsha) for parent in commit.parents],
                files_changed=[item.a_path or item.b_path for item in commit.diff(commit.parents[0] if commit.parents else None)]
            )
        except Exception:
            return None

    async def preload_commits(self, commit_ids: List[CommitId]) -> None:
        """Preload specific commits into cache."""
        tasks = []
        for commit_id in commit_ids:
            if commit_id.value not in self.loaded_commits:
                tasks.append(self.load_commit_info(commit_id.value))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for commit_id, result in zip(commit_ids, results):
                if isinstance(result, CommitInfo):
                    self.commit_cache[commit_id.value] = result
                    self.loaded_commits.add(commit_id.value)
```

### Async Operations

```python
from abc import ABC, abstractmethod
import asyncio
from typing import Tuple

class GitService(ABC):
    """Abstract git service interface."""

    @abstractmethod
    async def apply_operation(
        self,
        repo: Repository,
        operation: Operation
    ) -> OperationResult:
        """Apply an operation to the repository."""
        pass

class GitServiceImpl(GitService):
    """Implementation of GitService with async operations."""

    async def apply_operation(
        self,
        repo: Repository,
        operation: Operation
    ) -> OperationResult:
        """Apply operation with parallel processing where possible."""

        if isinstance(operation, MovePatch):
            # Run patch extraction and target preparation in parallel
            patch_task = self.extract_patch(
                repo, operation.from_commit, operation.patch_id
            )
            target_task = self.prepare_target_commit(repo, operation.to_commit)

            try:
                patch, target_state = await asyncio.gather(patch_task, target_task)

                # Apply patch to target
                result = await self.apply_patch_async(repo, patch, target_state)
                return result

            except Exception as e:
                raise GitError(f"Failed to apply MovePatch operation") from e

        elif isinstance(operation, SplitCommit):
            return await self._apply_split_commit(repo, operation)

        elif isinstance(operation, CreateCommit):
            return await self._apply_create_commit(repo, operation)

        elif isinstance(operation, MergeCommits):
            return await self._apply_merge_commits(repo, operation)

        else:
            raise PatchError(f"Unsupported operation type: {type(operation)}")

    async def extract_patch(
        self,
        repo: Repository,
        commit_id: CommitId,
        patch_id: PatchId
    ) -> Patch:
        """Extract a specific patch from a commit."""
        # Implementation would use asyncio.to_thread for CPU-bound work
        def _extract():
            # Actual patch extraction logic
            pass

        return await asyncio.to_thread(_extract)

    async def prepare_target_commit(
        self,
        repo: Repository,
        commit_id: CommitId
    ) -> Dict[str, Any]:
        """Prepare target commit state for patch application."""
        def _prepare():
            # Prepare target commit state
            return {"commit_id": commit_id, "prepared": True}

        return await asyncio.to_thread(_prepare)

    async def apply_patch_async(
        self,
        repo: Repository,
        patch: Patch,
        target_state: Dict[str, Any]
    ) -> OperationResult:
        """Apply patch to target with async processing."""
        def _apply():
            # Actual patch application logic
            return OperationResult(
                success=True,
                new_commit_ids=[CommitId("new_commit_id")],
                modified_commits=[],
                conflicts=[],
                message="Patch applied successfully"
            )

        return await asyncio.to_thread(_apply)

    async def _apply_split_commit(
        self,
        repo: Repository,
        operation: SplitCommit
    ) -> OperationResult:
        """Apply split commit operation."""
        # Extract all patches from source commit
        patches = await self.extract_patches(repo, operation.source_commit)

        # Create new commits from specified patch groups
        new_commit_tasks = []
        for new_commit in operation.new_commits:
            task = self.create_commit_from_patches(
                repo,
                [p for p in patches if p.id in new_commit.patches],
                new_commit.message
            )
            new_commit_tasks.append(task)

        try:
            new_commit_ids = await asyncio.gather(*new_commit_tasks)

            return OperationResult(
                success=True,
                new_commit_ids=new_commit_ids,
                modified_commits=[operation.source_commit],
                conflicts=[],
                message=f"Split commit into {len(new_commit_ids)} new commits"
            )
        except Exception as e:
            raise GitError("Failed to split commit") from e
```

## Testing Strategy

### Unit Test Structure

```python
import pytest
import tempfile
from pathlib import Path
from git import Repo
from git_patchdance.core.models import CommitId, CommitInfo
from git_patchdance.git.service import GitServiceImpl
from git_patchdance.diff.engine import DiffEngine

class TestRepository:
    """Helper class for creating test repositories."""

    def __init__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name)
        self.repo = Repo.init(self.path)
        self.commits = []

        # Configure git user for tests
        with self.repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

    def create_commit(self, message: str, files: dict[str, str]) -> str:
        """Create a commit with specified files and content."""
        # Write files
        for file_path, content in files.items():
            full_path = self.path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Stage and commit
        self.repo.index.add(list(files.keys()))
        commit = self.repo.index.commit(message)
        self.commits.append(commit.hexsha)
        return commit.hexsha

    def cleanup(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

@pytest.fixture
def test_repo():
    """Pytest fixture for test repository."""
    repo = TestRepository()
    yield repo
    repo.cleanup()

class TestPatchExtraction:
    """Tests for patch extraction functionality."""

    @pytest.mark.asyncio
    async def test_patch_extraction(self, test_repo):
        """Test basic patch extraction from commit."""
        # Create test commit
        commit_id = test_repo.create_commit("Test commit", {
            "file1.txt": "line1\nline2\nline3",
            "file2.txt": "content2"
        })

        # Extract patches
        diff_engine = DiffEngine()
        repository = Repository(
            path=test_repo.path,
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId(commit_id)
        )

        patches = await diff_engine.extract_patches_from_commit(
            repository, CommitId(commit_id)
        )

        # Verify results
        assert len(patches) == 2
        file_paths = {patch.target_file.name for patch in patches}
        assert file_paths == {"file1.txt", "file2.txt"}

    @pytest.mark.asyncio
    async def test_patch_extraction_with_modifications(self, test_repo):
        """Test patch extraction with file modifications."""
        # Create initial commit
        initial_commit = test_repo.create_commit("Initial", {
            "file1.txt": "original content"
        })

        # Create modified commit
        modified_commit = test_repo.create_commit("Modified", {
            "file1.txt": "modified content"
        })

        # Extract patches from modification
        diff_engine = DiffEngine()
        repository = Repository(
            path=test_repo.path,
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId(modified_commit)
        )

        patches = await diff_engine.extract_patches_from_commit(
            repository, CommitId(modified_commit)
        )

        # Verify modification was captured
        assert len(patches) == 1
        assert patches[0].target_file.name == "file1.txt"
        assert len(patches[0].hunks) > 0

class TestGitService:
    """Tests for GitService functionality."""

    @pytest.mark.asyncio
    async def test_open_repository(self, test_repo):
        """Test opening a git repository."""
        git_service = GitServiceImpl()
        repository = await git_service.open_repository(test_repo.path)

        assert repository.path == test_repo.path
        assert repository.current_branch == "main"

    @pytest.mark.asyncio
    async def test_get_commit_graph(self, test_repo):
        """Test retrieving commit graph."""
        # Create multiple commits
        commit1 = test_repo.create_commit("First", {"file1.txt": "content1"})
        commit2 = test_repo.create_commit("Second", {"file2.txt": "content2"})

        git_service = GitServiceImpl()
        repository = await git_service.open_repository(test_repo.path)
        commit_graph = await git_service.get_commit_graph(repository, limit=10)

        assert len(commit_graph.commits) == 2
        assert commit_graph.current_branch == "main"

        # Verify commits are in reverse chronological order
        commit_ids = [commit.id.value for commit in commit_graph.commits]
        assert commit_ids == [commit2, commit1]
```

### Integration Test Framework

```python
import pytest
import asyncio
from pathlib import Path
from git_patchdance.patch.manager import PatchManager
from git_patchdance.git.service import GitServiceImpl
from git_patchdance.core.models import (
    MovePatch, CommitId, PatchId, InsertPosition, Repository
)

class TestIntegration:
    """Integration tests for full workflows."""

    @pytest.mark.asyncio
    async def test_full_patch_workflow(self, test_repo):
        """Test complete patch workflow from extraction to application."""
        # 1. Create test repository with history
        commit1 = test_repo.create_commit("First commit", {
            "file1.txt": "original content\nline 2\nline 3"
        })
        commit2 = test_repo.create_commit("Second commit", {
            "file2.txt": "another file content"
        })
        commit3 = test_repo.create_commit("Third commit", {
            "file1.txt": "modified content\nline 2\nline 3\nnew line"
        })

        # 2. Initialize services
        git_service = GitServiceImpl()
        patch_manager = PatchManager(git_service)

        repository = Repository(
            path=test_repo.path,
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId(commit3)
        )

        # 3. Extract patches from commit
        patches = await patch_manager.extract_patches(repository, CommitId(commit3))
        assert len(patches) > 0

        # 4. Execute patch move operation
        operation = MovePatch(
            patch_id=patches[0].id,
            from_commit=CommitId(commit3),
            to_commit=CommitId(commit2),
            position=InsertPosition.AFTER
        )

        result = await patch_manager.apply_operation(repository, operation)

        # 5. Verify results
        assert result.success
        assert len(result.conflicts) == 0
        assert len(result.new_commit_ids) > 0

    @pytest.mark.asyncio
    async def test_conflict_detection_workflow(self, test_repo):
        """Test workflow with conflict detection."""
        # Create conflicting changes
        commit1 = test_repo.create_commit("Base", {
            "shared.txt": "line 1\nline 2\nline 3"
        })

        commit2 = test_repo.create_commit("Change A", {
            "shared.txt": "line 1\nmodified line 2\nline 3"
        })

        commit3 = test_repo.create_commit("Change B", {
            "shared.txt": "line 1\nline 2\ndifferent modification\nline 3"
        })

        # Initialize services
        git_service = GitServiceImpl()
        patch_manager = PatchManager(git_service)

        repository = Repository(
            path=test_repo.path,
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId(commit3)
        )

        # Extract patches from both commits
        patches_a = await patch_manager.extract_patches(repository, CommitId(commit2))
        patches_b = await patch_manager.extract_patches(repository, CommitId(commit3))

        # Detect conflicts
        conflicts = await patch_manager.detect_conflicts(
            repository, patches_a + patches_b, CommitId(commit1)
        )

        # Verify conflict detection
        assert len(conflicts) > 0
        assert conflicts[0].file_path.name == "shared.txt"

    @pytest.mark.asyncio
    async def test_commit_splitting_workflow(self, test_repo):
        """Test splitting a commit into multiple commits."""
        # Create commit with multiple file changes
        large_commit = test_repo.create_commit("Large commit", {
            "feature1.py": "# Feature 1 implementation\nclass Feature1:\n    pass",
            "feature2.py": "# Feature 2 implementation\nclass Feature2:\n    pass",
            "tests.py": "# Tests for both features\nimport unittest"
        })

        # Initialize services
        git_service = GitServiceImpl()
        patch_manager = PatchManager(git_service)

        repository = Repository(
            path=test_repo.path,
            current_branch="main",
            is_dirty=False,
            head_commit=CommitId(large_commit)
        )

        # Extract all patches from the large commit
        patches = await patch_manager.extract_patches(repository, CommitId(large_commit))
        assert len(patches) == 3

        # Group patches for splitting
        feature1_patches = [p for p in patches if "feature1" in str(p.target_file)]
        feature2_patches = [p for p in patches if "feature2" in str(p.target_file)]
        test_patches = [p for p in patches if "tests" in str(p.target_file)]

        # Create new commits from patch groups
        if feature1_patches:
            commit1 = await patch_manager.create_commit_from_patches(
                repository, feature1_patches, "Add Feature 1"
            )
            assert commit1 is not None

        if feature2_patches:
            commit2 = await patch_manager.create_commit_from_patches(
                repository, feature2_patches, "Add Feature 2"
            )
            assert commit2 is not None

        if test_patches:
            commit3 = await patch_manager.create_commit_from_patches(
                repository, test_patches, "Add tests"
            )
            assert commit3 is not None

@pytest.mark.slow
class TestPerformance:
    """Performance tests for large repositories."""

    @pytest.mark.asyncio
    async def test_large_repository_performance(self):
        """Test performance with large number of commits."""
        # This would create a repository with many commits
        # and measure performance of operations
        pass

    @pytest.mark.asyncio
    async def test_memory_usage_large_diffs(self):
        """Test memory usage with large diffs."""
        # This would test memory efficiency with large patches
        pass
```
