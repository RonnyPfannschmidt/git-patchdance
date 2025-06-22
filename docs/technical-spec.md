# Technical Specification

This document provides detailed implementation specifications for Git Patchdance, covering API design, data structures, algorithms, and technical implementation details.

## Core Data Structures

### Repository Model

```rust
#[derive(Debug, Clone)]
pub struct Repository {
    pub path: PathBuf,
    pub git_repo: git2::Repository,
    pub current_branch: String,
    pub is_dirty: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CommitId(pub git2::Oid);

#[derive(Debug, Clone)]
pub struct CommitInfo {
    pub id: CommitId,
    pub message: String,
    pub author: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub parent_ids: Vec<CommitId>,
    pub files_changed: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct CommitGraph {
    pub commits: HashMap<CommitId, CommitInfo>,
    pub edges: HashMap<CommitId, Vec<CommitId>>,
    pub heads: Vec<CommitId>,
}
```

### Patch Model

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct PatchId(pub String);

#[derive(Debug, Clone)]
pub struct Patch {
    pub id: PatchId,
    pub source_commit: CommitId,
    pub target_file: PathBuf,
    pub hunks: Vec<Hunk>,
    pub mode_change: Option<ModeChange>,
}

#[derive(Debug, Clone)]
pub struct Hunk {
    pub old_start: u32,
    pub old_lines: u32,
    pub new_start: u32,
    pub new_lines: u32,
    pub lines: Vec<DiffLine>,
    pub context: String,
}

#[derive(Debug, Clone)]
pub enum DiffLine {
    Context(String),
    Addition(String),
    Deletion(String),
}

#[derive(Debug, Clone)]
pub enum ModeChange {
    NewFile { mode: u32 },
    DeletedFile { mode: u32 },
    ModeChange { old_mode: u32, new_mode: u32 },
}
```

### Operation Model

```rust
#[derive(Debug, Clone)]
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
    MergeCommits {
        commit_ids: Vec<CommitId>,
        message: String,
    },
}

#[derive(Debug, Clone)]
pub struct NewCommit {
    pub message: String,
    pub patches: Vec<PatchId>,
    pub position: InsertPosition,
}

#[derive(Debug, Clone)]
pub enum InsertPosition {
    Before(CommitId),
    After(CommitId),
    AtBranchHead,
}
```

## API Design

### Core Services

#### GitService

```rust
#[async_trait]
pub trait GitService {
    async fn open_repository(&self, path: &Path) -> Result<Repository>;
    async fn get_commit_graph(&self, repo: &Repository) -> Result<CommitGraph>;
    async fn get_commit_diff(&self, repo: &Repository, commit_id: &CommitId) -> Result<Vec<Patch>>;
    async fn apply_operation(&self, repo: &Repository, operation: Operation) -> Result<OperationResult>;
    async fn preview_operation(&self, repo: &Repository, operation: Operation) -> Result<OperationPreview>;
}

pub struct GitServiceImpl {
    cache: Arc<RwLock<GitCache>>,
}

#[derive(Debug)]
pub struct OperationResult {
    pub success: bool,
    pub new_commit_ids: Vec<CommitId>,
    pub modified_commits: Vec<CommitId>,
    pub conflicts: Vec<Conflict>,
}

#[derive(Debug)]
pub struct OperationPreview {
    pub changes: Vec<PreviewChange>,
    pub potential_conflicts: Vec<Conflict>,
    pub affected_commits: Vec<CommitId>,
}
```

#### PatchManager

```rust
pub struct PatchManager {
    git_service: Arc<dyn GitService>,
    diff_engine: DiffEngine,
}

impl PatchManager {
    pub async fn extract_patches(&self, repo: &Repository, commit_id: &CommitId) -> Result<Vec<Patch>>;
    pub async fn apply_patches(&self, repo: &Repository, patches: &[Patch], target: &CommitId) -> Result<CommitId>;
    pub async fn create_commit_from_patches(&self, repo: &Repository, patches: &[Patch], message: &str) -> Result<CommitId>;
    pub async fn detect_conflicts(&self, repo: &Repository, patches: &[Patch], target: &CommitId) -> Result<Vec<Conflict>>;
}
```

#### DiffEngine

```rust
pub struct DiffEngine;

impl DiffEngine {
    pub fn parse_diff(&self, diff_text: &str) -> Result<Vec<Patch>>;
    pub fn apply_patch(&self, original: &str, patch: &Patch) -> Result<String>;
    pub fn merge_patches(&self, patches: &[Patch]) -> Result<Patch>;
    pub fn detect_conflicts(&self, patch1: &Patch, patch2: &Patch) -> Vec<Conflict>;
    pub fn resolve_conflict(&self, conflict: &Conflict, resolution: ConflictResolution) -> Result<Patch>;
}

#[derive(Debug, Clone)]
pub struct Conflict {
    pub id: String,
    pub kind: ConflictKind,
    pub file_path: PathBuf,
    pub description: String,
    pub our_content: String,
    pub their_content: String,
}

#[derive(Debug, Clone)]
pub enum ConflictKind {
    ContentConflict,
    ModeConflict,
    DeleteModifyConflict,
    RenameConflict,
}
```

## Algorithm Specifications

### Patch Extraction Algorithm

```rust
impl DiffEngine {
    pub fn extract_patches_from_commit(&self, repo: &git2::Repository, commit: &git2::Commit) -> Result<Vec<Patch>> {
        let mut patches = Vec::new();
        
        // Get parent commit (handle initial commit case)
        let parent = match commit.parent_count() {
            0 => None,
            _ => Some(commit.parent(0)?),
        };
        
        // Generate diff between commit and parent
        let diff = if let Some(parent) = parent {
            repo.diff_tree_to_tree(
                Some(&parent.tree()?),
                Some(&commit.tree()?),
                None,
            )?
        } else {
            repo.diff_tree_to_tree(None, Some(&commit.tree()?), None)?
        };
        
        // Process each delta (file change)
        diff.foreach(
            &mut |delta, _progress| {
                if let Some(patch) = self.process_delta(delta) {
                    patches.push(patch);
                }
                true
            },
            None,
            None,
            Some(&mut |delta, hunk, line| {
                // Process individual lines within hunks
                self.process_diff_line(delta, hunk, line);
                true
            }),
        )?;
        
        Ok(patches)
    }
}
```

### Patch Application Algorithm

```rust
impl PatchManager {
    pub async fn apply_patch_to_commit(&self, repo: &Repository, patch: &Patch, target_commit: &CommitId) -> Result<CommitId> {
        // 1. Create a new index based on target commit
        let mut index = repo.git_repo.index()?;
        let target_tree = repo.git_repo.find_commit(target_commit.0)?.tree()?;
        index.read_tree(&target_tree)?;
        
        // 2. Apply patch to working directory
        let temp_dir = self.create_temp_workspace(repo, target_commit).await?;
        self.apply_patch_to_files(&temp_dir, patch).await?;
        
        // 3. Stage changes
        for file_path in &patch.affected_files() {
            index.add_path(file_path)?;
        }
        
        // 4. Create new commit
        let tree_id = index.write_tree()?;
        let tree = repo.git_repo.find_tree(tree_id)?;
        let parent_commit = repo.git_repo.find_commit(target_commit.0)?;
        
        let signature = repo.git_repo.signature()?;
        let commit_id = repo.git_repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            &format!("Apply patch from {}", patch.source_commit.0),
            &tree,
            &[&parent_commit],
        )?;
        
        Ok(CommitId(commit_id))
    }
}
```

### Conflict Detection Algorithm

```rust
impl DiffEngine {
    pub fn detect_patch_conflicts(&self, patches: &[Patch]) -> Vec<Conflict> {
        let mut conflicts = Vec::new();
        
        // Build line-level change map
        let mut line_changes: HashMap<(PathBuf, u32), Vec<&Patch>> = HashMap::new();
        
        for patch in patches {
            for hunk in &patch.hunks {
                // Map each affected line to the patches that modify it
                for line_no in hunk.old_start..hunk.old_start + hunk.old_lines {
                    line_changes
                        .entry((patch.target_file.clone(), line_no))
                        .or_default()
                        .push(patch);
                }
            }
        }
        
        // Detect conflicts where multiple patches modify same lines
        for ((file_path, line_no), modifying_patches) in line_changes {
            if modifying_patches.len() > 1 {
                conflicts.push(Conflict {
                    id: format!("{}:{}", file_path.display(), line_no),
                    kind: ConflictKind::ContentConflict,
                    file_path: file_path.clone(),
                    description: format!(
                        "Line {} modified by {} patches", 
                        line_no, 
                        modifying_patches.len()
                    ),
                    our_content: self.extract_patch_content(modifying_patches[0]),
                    their_content: self.extract_patch_content(modifying_patches[1]),
                });
            }
        }
        
        conflicts
    }
}
```

## Caching Strategy

### GitCache Implementation

```rust
#[derive(Debug)]
pub struct GitCache {
    commits: LruCache<CommitId, CommitInfo>,
    patches: LruCache<CommitId, Vec<Patch>>,
    diffs: LruCache<(CommitId, CommitId), String>,
    trees: LruCache<CommitId, git2::Tree>,
}

impl GitCache {
    pub fn new(capacity: usize) -> Self {
        Self {
            commits: LruCache::new(capacity),
            patches: LruCache::new(capacity),
            diffs: LruCache::new(capacity),
            trees: LruCache::new(capacity),
        }
    }
    
    pub fn get_commit(&mut self, id: &CommitId) -> Option<&CommitInfo> {
        self.commits.get(id)
    }
    
    pub fn cache_commit(&mut self, id: CommitId, info: CommitInfo) {
        self.commits.put(id, info);
    }
    
    pub fn invalidate_commit(&mut self, id: &CommitId) {
        self.commits.pop(id);
        self.patches.pop(id);
        // Invalidate related diff cache entries
        self.diffs.retain(|&(from, to), _| from != *id && to != *id);
    }
}
```

## Error Handling

### Error Types

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

pub type Result<T> = std::result::Result<T, GitPatchError>;
```

### Error Recovery

```rust
impl PatchManager {
    pub async fn recover_from_failed_operation(&self, repo: &Repository, operation_id: &str) -> Result<()> {
        // 1. Load operation state from backup
        let backup_state = self.load_operation_backup(operation_id)?;
        
        // 2. Rollback git changes
        self.rollback_git_changes(repo, &backup_state).await?;
        
        // 3. Clean up temporary files
        self.cleanup_temp_files(&backup_state).await?;
        
        // 4. Reset application state
        self.reset_app_state(&backup_state).await?;
        
        Ok(())
    }
}
```

## Performance Optimizations

### Lazy Loading Strategy

```rust
pub struct LazyCommitGraph {
    repo: Repository,
    loaded_commits: HashSet<CommitId>,
    commit_cache: HashMap<CommitId, CommitInfo>,
    loading_queue: VecDeque<CommitId>,
}

impl LazyCommitGraph {
    pub async fn load_commit_range(&mut self, start: CommitId, count: usize) -> Result<Vec<CommitInfo>> {
        let mut commits = Vec::new();
        let mut current = start;
        
        for _ in 0..count {
            if !self.loaded_commits.contains(&current) {
                let info = self.load_commit_info(&current).await?;
                self.commit_cache.insert(current.clone(), info.clone());
                self.loaded_commits.insert(current.clone());
                commits.push(info);
            } else {
                commits.push(self.commit_cache[&current].clone());
            }
            
            // Move to next commit
            if let Some(parent) = self.get_first_parent(&current)? {
                current = parent;
            } else {
                break;
            }
        }
        
        Ok(commits)
    }
}
```

### Async Operations

```rust
impl GitService for GitServiceImpl {
    async fn apply_operation(&self, repo: &Repository, operation: Operation) -> Result<OperationResult> {
        match operation {
            Operation::MovePatch { patch_id, from_commit, to_commit, position } => {
                // Run patch extraction and application in parallel
                let (patch, target_state) = tokio::try_join!(
                    self.extract_patch(repo, &from_commit, &patch_id),
                    self.prepare_target_commit(repo, &to_commit)
                )?;
                
                // Apply patch to target
                let result = self.apply_patch_async(repo, &patch, &target_state).await?;
                Ok(result)
            }
            _ => todo!("Implement other operations"),
        }
    }
}
```

## Testing Strategy

### Unit Test Structure

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    
    struct TestRepository {
        temp_dir: TempDir,
        repo: git2::Repository,
    }
    
    impl TestRepository {
        fn new() -> Result<Self> {
            let temp_dir = TempDir::new()?;
            let repo = git2::Repository::init(temp_dir.path())?;
            Ok(Self { temp_dir, repo })
        }
        
        fn create_commit(&self, message: &str, files: &[(&str, &str)]) -> Result<git2::Oid> {
            // Helper to create test commits
            // Implementation details...
        }
    }
    
    #[tokio::test]
    async fn test_patch_extraction() {
        let test_repo = TestRepository::new().unwrap();
        let commit_id = test_repo.create_commit("Test commit", &[
            ("file1.txt", "line1\nline2\nline3"),
            ("file2.txt", "content2"),
        ]).unwrap();
        
        let diff_engine = DiffEngine::new();
        let patches = diff_engine.extract_patches_from_commit(&test_repo.repo, &commit_id).unwrap();
        
        assert_eq!(patches.len(), 2);
        assert_eq!(patches[0].target_file, PathBuf::from("file1.txt"));
    }
}
```

### Integration Test Framework

```rust
#[cfg(test)]
mod integration_tests {
    use super::*;
    
    #[tokio::test]
    async fn test_full_patch_workflow() {
        // 1. Create test repository with multiple commits
        let test_repo = create_test_repo_with_history().await;
        
        // 2. Initialize services
        let git_service = GitServiceImpl::new();
        let patch_manager = PatchManager::new(Arc::new(git_service));
        
        // 3. Execute patch move operation
        let operation = Operation::MovePatch {
            patch_id: PatchId("test-patch".to_string()),
            from_commit: CommitId(test_repo.commits[0]),
            to_commit: CommitId(test_repo.commits[1]),
            position: InsertPosition::After(CommitId(test_repo.commits[1])),
        };
        
        let result = patch_manager.apply_operation(&test_repo.repo, operation).await;
        
        // 4. Verify results
        assert!(result.is_ok());
        let operation_result = result.unwrap();
        assert!(operation_result.success);
        assert_eq!(operation_result.conflicts.len(), 0);
    }
}
```