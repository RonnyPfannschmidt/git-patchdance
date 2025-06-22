# API Reference

This document provides a comprehensive reference for Git Patchdance's public APIs. For detailed implementation examples, see the [Technical Specification](technical-spec.md).

## Core Types

### Repository Types

#### `Repository`
Represents a git repository and its current state.

```rust
pub struct Repository {
    pub path: PathBuf,
    pub current_branch: String,
    pub is_dirty: bool,
}
```

#### `CommitId`
Unique identifier for a git commit.

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CommitId(pub git2::Oid);
```

#### `CommitInfo`
Metadata about a git commit.

```rust
pub struct CommitInfo {
    pub id: CommitId,
    pub message: String,
    pub author: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub parent_ids: Vec<CommitId>,
    pub files_changed: Vec<String>,
}
```

### Patch Types

#### `Patch`
Represents a single file change that can be moved between commits.

```rust
pub struct Patch {
    pub id: PatchId,
    pub source_commit: CommitId,
    pub target_file: PathBuf,
    pub hunks: Vec<Hunk>,
    pub mode_change: Option<ModeChange>,
}
```

#### `Hunk`
A contiguous block of changes within a file.

```rust
pub struct Hunk {
    pub old_start: u32,
    pub old_lines: u32,
    pub new_start: u32,
    pub new_lines: u32,
    pub lines: Vec<DiffLine>,
    pub context: String,
}
```

### Operation Types

#### `Operation`
High-level operations that can be performed on patches.

```rust
pub enum Operation {
    MovePatch {
        patch_id: PatchId,
        from_commit: CommitId,
        to_commit: CommitId,
        position: InsertPosition,
    },
    SplitCommit {
        source_commit: CommitId,
        new_commits: Vec<NewCommit>,
    },
    CreateCommit {
        patches: Vec<PatchId>,
        message: String,
        position: InsertPosition,
    },
}
```

## Core Services

### GitService

Primary interface for git repository operations.

#### Methods

##### `open_repository`
Opens a git repository at the specified path.

```rust
async fn open_repository(&self, path: &Path) -> Result<Repository>
```

**Parameters:**
- `path`: Path to the git repository

**Returns:**
- `Ok(Repository)`: Successfully opened repository
- `Err(GitPatchError)`: Repository not found or invalid

**Example:**
```rust
let git_service = GitService::new();
let repo = git_service.open_repository(Path::new("/path/to/repo")).await?;
```

##### `get_commit_graph`
Retrieves the commit graph for the repository.

```rust
async fn get_commit_graph(&self, repo: &Repository) -> Result<CommitGraph>
```

**Parameters:**
- `repo`: Repository to analyze

**Returns:**
- `Ok(CommitGraph)`: Complete commit graph
- `Err(GitPatchError)`: Failed to read git history

##### `get_commit_diff`
Gets the diff for a specific commit.

```rust
async fn get_commit_diff(&self, repo: &Repository, commit_id: &CommitId) -> Result<Vec<Patch>>
```

**Parameters:**
- `repo`: Repository containing the commit
- `commit_id`: Commit to analyze

**Returns:**
- `Ok(Vec<Patch>)`: Patches representing the commit's changes
- `Err(GitPatchError)`: Invalid commit or git error

##### `apply_operation`
Applies a patch operation to the repository.

```rust
async fn apply_operation(&self, repo: &Repository, operation: Operation) -> Result<OperationResult>
```

**Parameters:**
- `repo`: Target repository
- `operation`: Operation to perform

**Returns:**
- `Ok(OperationResult)`: Operation completed successfully
- `Err(GitPatchError)`: Operation failed

##### `preview_operation`
Previews the effects of an operation without applying it.

```rust
async fn preview_operation(&self, repo: &Repository, operation: Operation) -> Result<OperationPreview>
```

### PatchManager

High-level interface for patch manipulation.

#### Methods

##### `extract_patches`
Extracts patches from a commit.

```rust
async fn extract_patches(&self, repo: &Repository, commit_id: &CommitId) -> Result<Vec<Patch>>
```

**Parameters:**
- `repo`: Repository containing the commit
- `commit_id`: Commit to extract patches from

**Returns:**
- `Ok(Vec<Patch>)`: Extracted patches
- `Err(GitPatchError)`: Extraction failed

##### `apply_patches`
Applies patches to a target commit.

```rust
async fn apply_patches(&self, repo: &Repository, patches: &[Patch], target: &CommitId) -> Result<CommitId>
```

**Parameters:**
- `repo`: Target repository
- `patches`: Patches to apply
- `target`: Target commit to apply patches to

**Returns:**
- `Ok(CommitId)`: New commit ID with patches applied
- `Err(GitPatchError)`: Application failed

##### `create_commit_from_patches`
Creates a new commit from a collection of patches.

```rust
async fn create_commit_from_patches(&self, repo: &Repository, patches: &[Patch], message: &str) -> Result<CommitId>
```

**Parameters:**
- `repo`: Target repository
- `patches`: Patches to include in the new commit
- `message`: Commit message

**Returns:**
- `Ok(CommitId)`: New commit ID
- `Err(GitPatchError)`: Commit creation failed

##### `detect_conflicts`
Detects potential conflicts when applying patches.

```rust
async fn detect_conflicts(&self, repo: &Repository, patches: &[Patch], target: &CommitId) -> Result<Vec<Conflict>>
```

**Parameters:**
- `repo`: Target repository
- `patches`: Patches to analyze
- `target`: Target commit

**Returns:**
- `Ok(Vec<Conflict>)`: List of detected conflicts
- `Err(GitPatchError)`: Analysis failed

### DiffEngine

Low-level diff parsing and manipulation.

#### Methods

##### `parse_diff`
Parses a git diff into patch objects.

```rust
fn parse_diff(&self, diff_text: &str) -> Result<Vec<Patch>>
```

**Parameters:**
- `diff_text`: Raw git diff text

**Returns:**
- `Ok(Vec<Patch>)`: Parsed patches
- `Err(GitPatchError)`: Parse error

##### `apply_patch`
Applies a patch to file content.

```rust
fn apply_patch(&self, original: &str, patch: &Patch) -> Result<String>
```

**Parameters:**
- `original`: Original file content
- `patch`: Patch to apply

**Returns:**
- `Ok(String)`: Modified content
- `Err(GitPatchError)`: Application failed

##### `merge_patches`
Merges multiple patches affecting the same file.

```rust
fn merge_patches(&self, patches: &[Patch]) -> Result<Patch>
```

**Parameters:**
- `patches`: Patches to merge

**Returns:**
- `Ok(Patch)`: Merged patch
- `Err(GitPatchError)`: Merge failed due to conflicts

##### `detect_conflicts`
Detects conflicts between patches.

```rust
fn detect_conflicts(&self, patch1: &Patch, patch2: &Patch) -> Vec<Conflict>
```

**Parameters:**
- `patch1`: First patch
- `patch2`: Second patch

**Returns:**
- `Vec<Conflict>`: List of conflicts

## Application API

### AppState

Central application state management.

```rust
pub struct AppState {
    pub repository: Option<Repository>,
    pub commit_history: Vec<CommitInfo>,
    pub selected_commits: HashSet<CommitId>,
    pub patch_operations: Vec<PatchOperation>,
    pub ui_state: UiState,
}
```

#### Methods

##### `new`
Creates a new application state.

```rust
pub fn new() -> Self
```

##### `load_repository`
Loads a repository into the application state.

```rust
pub async fn load_repository(&mut self, path: &Path) -> Result<()>
```

##### `select_commit`
Selects a commit for operations.

```rust
pub fn select_commit(&mut self, commit_id: CommitId)
```

##### `deselect_commit`
Deselects a commit.

```rust
pub fn deselect_commit(&mut self, commit_id: &CommitId)
```

##### `queue_operation`
Queues an operation for execution.

```rust
pub fn queue_operation(&mut self, operation: Operation)
```

### CommandHandler

Processes user commands and coordinates operations.

#### Methods

##### `execute_command`
Executes a user command.

```rust
pub async fn execute_command(&mut self, command: Command) -> Result<CommandResult>
```

**Parameters:**
- `command`: Command to execute

**Returns:**
- `Ok(CommandResult)`: Command completed
- `Err(GitPatchError)`: Command failed

## Error Types

### `GitPatchError`

Main error type for all Git Patchdance operations.

```rust
#[derive(Debug, thiserror::Error)]
pub enum GitPatchError {
    #[error("Git operation failed: {0}")]
    GitError(#[from] git2::Error),
    
    #[error("IO operation failed: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Patch application failed: {reason}")]
    PatchError { reason: String },
    
    #[error("Conflict detected: {description}")]
    ConflictError { description: String, conflicts: Vec<Conflict> },
    
    #[error("Repository not found at path: {path}")]
    RepositoryNotFound { path: PathBuf },
    
    #[error("Invalid commit ID: {id}")]
    InvalidCommitId { id: String },
    
    #[error("Operation cancelled by user")]
    OperationCancelled,
}
```

## Result Types

### `OperationResult`

Result of applying an operation.

```rust
pub struct OperationResult {
    pub success: bool,
    pub new_commit_ids: Vec<CommitId>,
    pub modified_commits: Vec<CommitId>,
    pub conflicts: Vec<Conflict>,
}
```

### `OperationPreview`

Preview of an operation's effects.

```rust
pub struct OperationPreview {
    pub changes: Vec<PreviewChange>,
    pub potential_conflicts: Vec<Conflict>,
    pub affected_commits: Vec<CommitId>,
}
```

### `Conflict`

Represents a conflict between operations.

```rust
pub struct Conflict {
    pub id: String,
    pub kind: ConflictKind,
    pub file_path: PathBuf,
    pub description: String,
    pub our_content: String,
    pub their_content: String,
}
```

## Configuration

### Configuration File Format

Git Patchdance uses TOML for configuration:

```toml
# ~/.config/git-patchdance/config.toml

[general]
default_editor = "vim"
auto_backup = true
max_history_size = 1000

[ui]
theme = "dark"
vim_mode = true
show_line_numbers = true

[git]
auto_stage = false
preserve_merge_commits = true
default_branch = "main"

[performance]
cache_size = 100
parallel_operations = true
streaming_threshold = 1000
```

### Configuration API

```rust
pub struct Config {
    pub general: GeneralConfig,
    pub ui: UiConfig,
    pub git: GitConfig,
    pub performance: PerformanceConfig,
}

impl Config {
    pub fn load() -> Result<Self>;
    pub fn save(&self) -> Result<()>;
    pub fn default() -> Self;
}
```

## Plugin System

### Plugin Trait

```rust
#[async_trait]
pub trait Plugin {
    fn name(&self) -> &str;
    fn version(&self) -> &str;
    
    async fn initialize(&mut self, context: &PluginContext) -> Result<()>;
    async fn handle_event(&self, event: &Event) -> Result<Option<Response>>;
    async fn shutdown(&self) -> Result<()>;
}
```

### Plugin Context

```rust
pub struct PluginContext {
    pub app_state: Arc<RwLock<AppState>>,
    pub git_service: Arc<dyn GitService>,
    pub patch_manager: Arc<PatchManager>,
}
```

## Integration Examples

### Basic Usage

```rust
use git_patchdance::{GitService, PatchManager, Operation, CommitId};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize services
    let git_service = GitService::new();
    let patch_manager = PatchManager::new(Arc::new(git_service));
    
    // Open repository
    let repo = git_service.open_repository(Path::new(".")).await?;
    
    // Get commit history
    let commits = git_service.get_commit_graph(&repo).await?;
    
    // Extract patches from a commit
    let patches = patch_manager.extract_patches(&repo, &commits.heads[0]).await?;
    
    // Move a patch to another commit
    let operation = Operation::MovePatch {
        patch_id: patches[0].id.clone(),
        from_commit: commits.heads[0].clone(),
        to_commit: commits.heads[1].clone(),
        position: InsertPosition::After(commits.heads[1].clone()),
    };
    
    let result = patch_manager.apply_operation(&repo, operation).await?;
    println!("Operation successful: {}", result.success);
    
    Ok(())
}
```

### Advanced Workflow

```rust
use git_patchdance::*;

async fn advanced_patch_workflow() -> Result<()> {
    let git_service = GitService::new();
    let patch_manager = PatchManager::new(Arc::new(git_service));
    let repo = git_service.open_repository(Path::new(".")).await?;
    
    // Find commits to work with
    let commits = git_service.get_commit_graph(&repo).await?;
    let source_commit = &commits.heads[0];
    let target_commit = &commits.heads[1];
    
    // Extract specific patches
    let all_patches = patch_manager.extract_patches(&repo, source_commit).await?;
    let filtered_patches: Vec<_> = all_patches
        .into_iter()
        .filter(|p| p.target_file.extension() == Some(std::ffi::OsStr::new("rs")))
        .collect();
    
    // Check for conflicts
    let conflicts = patch_manager
        .detect_conflicts(&repo, &filtered_patches, target_commit)
        .await?;
    
    if !conflicts.is_empty() {
        println!("Conflicts detected: {:?}", conflicts);
        // Handle conflicts...
        return Ok(());
    }
    
    // Apply patches
    let new_commit = patch_manager
        .apply_patches(&repo, &filtered_patches, target_commit)
        .await?;
    
    println!("Created new commit: {:?}", new_commit);
    Ok(())
}
```

## CLI Integration

### Command Line Interface

```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "git-patchdance")]
#[command(about = "Interactive git patch management")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
    
    #[arg(long, help = "Launch GUI mode")]
    pub gui: bool,
    
    #[arg(long, help = "Repository path")]
    pub repo: Option<PathBuf>,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Launch interactive mode
    Interactive,
    /// Move patches between commits
    Move {
        #[arg(help = "Source commit")]
        from: String,
        #[arg(help = "Target commit")]
        to: String,
        #[arg(long, help = "File filter")]
        files: Vec<String>,
    },
    /// Split a commit into multiple commits
    Split {
        #[arg(help = "Commit to split")]
        commit: String,
    },
}
```

---

*This API reference is generated from the codebase. For the most up-to-date information, refer to the inline documentation in the source code.*