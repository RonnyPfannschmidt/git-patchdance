# Git Integration and Patch Management

This document details how Git Patchdance integrates with git repositories and implements advanced patch management capabilities.

## Git Operations Overview

Git Patchdance leverages libgit2 through the `git2` Rust crate for robust, low-level git operations while maintaining safety and performance.

### Core Git Concepts

#### Repository State Management

```rust
pub struct RepositoryState {
    pub head_ref: String,
    pub current_branch: Option<String>,
    pub working_directory_clean: bool,
    pub staged_changes: bool,
    pub untracked_files: Vec<PathBuf>,
    pub stash_count: usize,
}

impl RepositoryState {
    pub fn is_safe_for_operations(&self) -> bool {
        self.working_directory_clean && !self.staged_changes
    }
}
```

#### Commit Navigation

```rust
pub struct CommitWalker {
    repo: git2::Repository,
    current: Option<git2::Oid>,
    visited: HashSet<git2::Oid>,
}

impl CommitWalker {
    pub fn new(repo: git2::Repository, start: git2::Oid) -> Self {
        Self {
            repo,
            current: Some(start),
            visited: HashSet::new(),
        }
    }

    pub fn walk_history(&mut self, max_count: usize) -> Result<Vec<CommitInfo>> {
        let mut commits = Vec::new();
        let mut count = 0;

        while let Some(oid) = self.current.take() {
            if count >= max_count || self.visited.contains(&oid) {
                break;
            }

            let commit = self.repo.find_commit(oid)?;
            commits.push(CommitInfo::from_git_commit(&commit)?);

            self.visited.insert(oid);
            self.current = commit.parent_ids().next();
            count += 1;
        }

        Ok(commits)
    }
}
```

## Patch Extraction and Analysis

### Diff Generation

Git Patchdance generates diffs at multiple levels to support fine-grained patch manipulation:

```rust
pub struct DiffGenerator {
    repo: git2::Repository,
}

impl DiffGenerator {
    pub fn generate_commit_diff(&self, commit_id: git2::Oid) -> Result<CommitDiff> {
        let commit = self.repo.find_commit(commit_id)?;
        let commit_tree = commit.tree()?;

        let parent_tree = match commit.parent_count() {
            0 => None,
            _ => Some(commit.parent(0)?.tree()?),
        };

        let diff = self.repo.diff_tree_to_tree(
            parent_tree.as_ref(),
            Some(&commit_tree),
            None,
        )?;

        Ok(CommitDiff::from_git_diff(diff, commit_id)?)
    }

    pub fn generate_range_diff(&self, from: git2::Oid, to: git2::Oid) -> Result<RangeDiff> {
        let from_commit = self.repo.find_commit(from)?;
        let to_commit = self.repo.find_commit(to)?;

        let diff = self.repo.diff_tree_to_tree(
            Some(&from_commit.tree()?),
            Some(&to_commit.tree()?),
            None,
        )?;

        Ok(RangeDiff::from_git_diff(diff, from, to)?)
    }
}
```

### Patch Parsing and Manipulation

```rust
#[derive(Debug, Clone)]
pub struct CommitDiff {
    pub commit_id: git2::Oid,
    pub files: Vec<FileDiff>,
    pub stats: DiffStats,
}

#[derive(Debug, Clone)]
pub struct FileDiff {
    pub old_path: Option<PathBuf>,
    pub new_path: Option<PathBuf>,
    pub status: FileStatus,
    pub hunks: Vec<DiffHunk>,
    pub binary: bool,
}

#[derive(Debug, Clone)]
pub enum FileStatus {
    Added,
    Deleted,
    Modified,
    Renamed { similarity: u16 },
    Copied { similarity: u16 },
    Typechange,
}

#[derive(Debug, Clone)]
pub struct DiffHunk {
    pub old_start: u32,
    pub old_lines: u32,
    pub new_start: u32,
    pub new_lines: u32,
    pub header: String,
    pub lines: Vec<DiffLine>,
}

impl DiffHunk {
    pub fn can_split(&self) -> bool {
        self.lines.len() > 1 && self.contains_context_lines()
    }

    pub fn split_at_line(&self, line_index: usize) -> Result<(DiffHunk, DiffHunk)> {
        if line_index >= self.lines.len() {
            return Err(GitPatchError::InvalidSplit);
        }

        // Implementation for splitting hunks
        // This is complex and requires careful line number recalculation
        todo!("Implement hunk splitting")
    }

    fn contains_context_lines(&self) -> bool {
        self.lines.iter().any(|line| matches!(line, DiffLine::Context(_)))
    }
}
```

## Advanced Patch Operations

### Patch Extraction Strategies

#### Full Commit Extraction
```rust
impl PatchExtractor {
    pub async fn extract_full_commit(&self, commit_id: git2::Oid) -> Result<CommitPatch> {
        let diff = self.diff_generator.generate_commit_diff(commit_id)?;

        Ok(CommitPatch {
            source_commit: commit_id,
            patches: diff.files.into_iter()
                .map(|file_diff| self.file_diff_to_patch(file_diff))
                .collect::<Result<Vec<_>>>()?,
        })
    }
}
```

#### Selective Patch Extraction
```rust
impl PatchExtractor {
    pub async fn extract_selective_patches(
        &self,
        commit_id: git2::Oid,
        file_filter: &[PathBuf],
        hunk_filter: Option<&dyn Fn(&DiffHunk) -> bool>
    ) -> Result<Vec<Patch>> {
        let diff = self.diff_generator.generate_commit_diff(commit_id)?;
        let mut patches = Vec::new();

        for file_diff in diff.files {
            // Filter by file path
            if !file_filter.is_empty() {
                let file_path = file_diff.new_path.as_ref()
                    .or(file_diff.old_path.as_ref())
                    .unwrap();

                if !file_filter.contains(file_path) {
                    continue;
                }
            }

            // Filter hunks if filter provided
            let hunks = if let Some(filter) = hunk_filter {
                file_diff.hunks.into_iter()
                    .filter(filter)
                    .collect()
            } else {
                file_diff.hunks
            };

            if !hunks.is_empty() {
                patches.push(Patch {
                    id: PatchId::new(&commit_id, &file_diff),
                    source_commit: CommitId(commit_id),
                    target_file: file_diff.new_path.unwrap_or_else(|| file_diff.old_path.unwrap()),
                    hunks,
                    mode_change: file_diff.mode_change,
                });
            }
        }

        Ok(patches)
    }
}
```

### Patch Application Algorithms

#### Three-Way Merge Algorithm
```rust
impl PatchApplicator {
    pub async fn apply_patch_with_merge(
        &self,
        repo: &git2::Repository,
        patch: &Patch,
        target_commit: git2::Oid,
    ) -> Result<ApplyResult> {
        // 1. Get the base version (where patch was extracted from)
        let base_content = self.get_file_content_at_commit(
            repo,
            &patch.target_file,
            patch.source_commit.0
        )?;

        // 2. Get the target version (where we want to apply)
        let target_content = self.get_file_content_at_commit(
            repo,
            &patch.target_file,
            target_commit
        )?;

        // 3. Apply patch to base to get "ours" version
        let our_content = self.apply_patch_to_content(&base_content, patch)?;

        // 4. Perform three-way merge
        let merge_result = self.three_way_merge(
            &base_content,
            &our_content,
            &target_content,
        )?;

        match merge_result {
            MergeResult::Clean(merged_content) => {
                Ok(ApplyResult::Success { content: merged_content })
            }
            MergeResult::Conflict(conflicts) => {
                Ok(ApplyResult::Conflict {
                    conflicts,
                    base: base_content,
                    ours: our_content,
                    theirs: target_content,
                })
            }
        }
    }

    fn three_way_merge(
        &self,
        base: &str,
        ours: &str,
        theirs: &str,
    ) -> Result<MergeResult> {
        // Implementation using similar algorithm to git's merge
        // This is a complex algorithm that requires careful implementation

        let base_lines: Vec<&str> = base.lines().collect();
        let our_lines: Vec<&str> = ours.lines().collect();
        let their_lines: Vec<&str> = theirs.lines().collect();

        // Use Myers' diff algorithm or similar to find changes
        let our_diff = self.diff_lines(&base_lines, &our_lines);
        let their_diff = self.diff_lines(&base_lines, &their_lines);

        // Merge the changes
        self.merge_diffs(&base_lines, our_diff, their_diff)
    }
}
```

#### Smart Patch Positioning
```rust
impl PatchApplicator {
    pub fn find_best_application_point(
        &self,
        file_content: &str,
        patch: &Patch,
    ) -> Result<Vec<ApplicationPoint>> {
        let mut candidates = Vec::new();
        let lines: Vec<&str> = file_content.lines().collect();

        for hunk in &patch.hunks {
            // Try exact match first
            if let Some(exact_pos) = self.find_exact_match(&lines, hunk) {
                candidates.push(ApplicationPoint {
                    hunk_index: 0, // simplified
                    line_offset: exact_pos,
                    confidence: 100,
                    match_type: MatchType::Exact,
                });
                continue;
            }

            // Try fuzzy matching with context
            let fuzzy_matches = self.find_fuzzy_matches(&lines, hunk, 3)?;
            candidates.extend(fuzzy_matches);
        }

        // Sort by confidence
        candidates.sort_by(|a, b| b.confidence.cmp(&a.confidence));
        Ok(candidates)
    }

    fn find_exact_match(&self, lines: &[&str], hunk: &DiffHunk) -> Option<u32> {
        let context_lines: Vec<&str> = hunk.lines.iter()
            .filter_map(|line| match line {
                DiffLine::Context(content) => Some(content.as_str()),
                DiffLine::Deletion(content) => Some(content.as_str()),
                _ => None,
            })
            .collect();

        if context_lines.is_empty() {
            return None;
        }

        // Search for exact sequence match
        for (i, window) in lines.windows(context_lines.len()).enumerate() {
            if window == context_lines.as_slice() {
                return Some(i as u32);
            }
        }

        None
    }
}
```

## Conflict Resolution

### Conflict Detection

```rust
#[derive(Debug, Clone)]
pub struct ConflictDetector;

impl ConflictDetector {
    pub fn detect_conflicts_in_patches(&self, patches: &[Patch]) -> Vec<PatchConflict> {
        let mut conflicts = Vec::new();
        let mut file_modifications: HashMap<PathBuf, Vec<(usize, &Patch)>> = HashMap::new();

        // Group patches by file
        for (patch_idx, patch) in patches.iter().enumerate() {
            file_modifications
                .entry(patch.target_file.clone())
                .or_default()
                .push((patch_idx, patch));
        }

        // Check for overlapping modifications in each file
        for (file_path, modifying_patches) in file_modifications {
            if modifying_patches.len() > 1 {
                let patch_conflicts = self.find_overlapping_hunks(&modifying_patches);
                conflicts.extend(patch_conflicts);
            }
        }

        conflicts
    }

    fn find_overlapping_hunks(&self, patches: &[(usize, &Patch)]) -> Vec<PatchConflict> {
        let mut conflicts = Vec::new();

        for i in 0..patches.len() {
            for j in i + 1..patches.len() {
                let (idx1, patch1) = patches[i];
                let (idx2, patch2) = patches[j];

                for (hunk1_idx, hunk1) in patch1.hunks.iter().enumerate() {
                    for (hunk2_idx, hunk2) in patch2.hunks.iter().enumerate() {
                        if self.hunks_overlap(hunk1, hunk2) {
                            conflicts.push(PatchConflict {
                                kind: ConflictKind::OverlappingHunks,
                                patch1_index: idx1,
                                patch2_index: idx2,
                                hunk1_index: hunk1_idx,
                                hunk2_index: hunk2_idx,
                                description: format!(
                                    "Hunks overlap in lines {}-{} and {}-{}",
                                    hunk1.old_start, hunk1.old_start + hunk1.old_lines,
                                    hunk2.old_start, hunk2.old_start + hunk2.old_lines
                                ),
                            });
                        }
                    }
                }
            }
        }

        conflicts
    }

    fn hunks_overlap(&self, hunk1: &DiffHunk, hunk2: &DiffHunk) -> bool {
        let hunk1_end = hunk1.old_start + hunk1.old_lines;
        let hunk2_end = hunk2.old_start + hunk2.old_lines;

        // Check if ranges overlap
        !(hunk1_end <= hunk2.old_start || hunk2_end <= hunk1.old_start)
    }
}
```

### Interactive Conflict Resolution

```rust
pub struct ConflictResolver {
    ui_handler: Arc<dyn ConflictUIHandler>,
}

#[async_trait]
pub trait ConflictUIHandler {
    async fn resolve_conflict(&self, conflict: &PatchConflict) -> Result<ConflictResolution>;
    async fn show_merge_editor(&self, merge_context: &MergeContext) -> Result<String>;
}

impl ConflictResolver {
    pub async fn resolve_patch_conflicts(
        &self,
        conflicts: &[PatchConflict],
        patches: &[Patch],
    ) -> Result<Vec<Patch>> {
        let mut resolved_patches = patches.to_vec();

        for conflict in conflicts {
            let resolution = self.ui_handler.resolve_conflict(conflict).await?;

            match resolution {
                ConflictResolution::KeepFirst => {
                    // Remove second patch's conflicting hunk
                    self.remove_conflicting_hunk(
                        &mut resolved_patches[conflict.patch2_index],
                        conflict.hunk2_index,
                    );
                }
                ConflictResolution::KeepSecond => {
                    // Remove first patch's conflicting hunk
                    self.remove_conflicting_hunk(
                        &mut resolved_patches[conflict.patch1_index],
                        conflict.hunk1_index,
                    );
                }
                ConflictResolution::Merge => {
                    // Launch interactive merge editor
                    let merged_content = self.interactive_merge(conflict, patches).await?;
                    self.apply_merged_content(&mut resolved_patches, conflict, merged_content);
                }
                ConflictResolution::Skip => {
                    // Skip both conflicting patches
                    resolved_patches[conflict.patch1_index].hunks.remove(conflict.hunk1_index);
                    resolved_patches[conflict.patch2_index].hunks.remove(conflict.hunk2_index);
                }
            }
        }

        // Remove empty patches
        resolved_patches.retain(|patch| !patch.hunks.is_empty());

        Ok(resolved_patches)
    }
}
```

## Git History Manipulation

### Safe History Rewriting

```rust
pub struct HistoryRewriter {
    repo: git2::Repository,
    backup_manager: BackupManager,
}

impl HistoryRewriter {
    pub async fn rewrite_commit_with_patches(
        &self,
        target_commit: git2::Oid,
        patches_to_add: &[Patch],
        patches_to_remove: &[PatchId],
    ) -> Result<git2::Oid> {
        // 1. Create backup point
        let backup_ref = self.backup_manager.create_backup(&self.repo, target_commit)?;

        // 2. Start rewrite transaction
        let transaction = self.start_rewrite_transaction(target_commit)?;

        match self.perform_rewrite(target_commit, patches_to_add, patches_to_remove).await {
            Ok(new_commit_id) => {
                transaction.commit()?;
                Ok(new_commit_id)
            }
            Err(e) => {
                transaction.rollback()?;
                self.backup_manager.restore_backup(&self.repo, &backup_ref)?;
                Err(e)
            }
        }
    }

    async fn perform_rewrite(
        &self,
        target_commit: git2::Oid,
        patches_to_add: &[Patch],
        patches_to_remove: &[PatchId],
    ) -> Result<git2::Oid> {
        // 1. Get original commit
        let original_commit = self.repo.find_commit(target_commit)?;

        // 2. Extract current patches from commit
        let mut current_patches = self.extract_patches_from_commit(target_commit)?;

        // 3. Remove specified patches
        current_patches.retain(|patch| !patches_to_remove.contains(&patch.id));

        // 4. Add new patches
        current_patches.extend_from_slice(patches_to_add);

        // 5. Create new tree from combined patches
        let new_tree = self.create_tree_from_patches(&current_patches, &original_commit.tree()?)?;

        // 6. Create new commit
        let signature = original_commit.author();
        let new_commit_id = self.repo.commit(
            None, // Don't update any reference yet
            signature,
            &original_commit.committer(),
            &original_commit.message().unwrap_or(""),
            &new_tree,
            &original_commit.parents().collect::<Vec<_>>(),
        )?;

        Ok(new_commit_id)
    }
}
```

### Branch Update Strategy

```rust
impl HistoryRewriter {
    pub async fn update_branch_after_rewrite(
        &self,
        branch_name: &str,
        old_commit: git2::Oid,
        new_commit: git2::Oid,
    ) -> Result<()> {
        // 1. Find all commits that need to be rebased
        let commits_to_rebase = self.find_descendant_commits(old_commit)?;

        // 2. Rebase each commit onto the new base
        let mut current_base = new_commit;

        for commit_to_rebase in commits_to_rebase {
            let rebased_commit = self.rebase_commit(commit_to_rebase, current_base).await?;
            current_base = rebased_commit;
        }

        // 3. Update branch reference
        let mut branch = self.repo.find_branch(branch_name, git2::BranchType::Local)?;
        branch.get_mut().set_target(current_base, "Rewrite history with patch operations")?;

        Ok(())
    }
}
```

## Performance Optimizations

### Streaming Large Diffs

```rust
pub struct StreamingDiffProcessor {
    chunk_size: usize,
}

impl StreamingDiffProcessor {
    pub async fn process_large_diff<F>(
        &self,
        diff: git2::Diff,
        processor: F,
    ) -> Result<()>
    where
        F: Fn(&git2::DiffDelta, &git2::DiffHunk, &git2::DiffLine) -> Result<()> + Send + 'static,
    {
        let (tx, mut rx) = mpsc::channel(self.chunk_size);

        // Spawn diff processing task
        let processor_task = tokio::spawn(async move {
            while let Some((delta, hunk, line)) = rx.recv().await {
                processor(&delta, &hunk, &line)?;
            }
            Ok::<(), GitPatchError>(())
        });

        // Stream diff data
        diff.foreach(
            &mut |delta, _progress| {
                // File-level callback
                true
            },
            None, // Binary callback
            Some(&mut |delta, hunk| {
                // Hunk-level callback
                true
            }),
            Some(&mut |delta, hunk, line| {
                // Line-level callback
                if let Err(_) = tx.try_send((delta.clone(), hunk.clone(), line.clone())) {
                    // Channel full, wait or handle backpressure
                    return false;
                }
                true
            }),
        )?;

        // Close channel and wait for processor
        drop(tx);
        processor_task.await??;

        Ok(())
    }
}
```

### Parallel Patch Processing

```rust
impl PatchManager {
    pub async fn apply_patches_parallel(
        &self,
        repo: &Repository,
        patches: Vec<Patch>,
        target_commit: CommitId,
    ) -> Result<Vec<ApplyResult>> {
        // Group patches by file to avoid conflicts
        let patches_by_file = self.group_patches_by_file(patches);

        // Process each file group in parallel
        let tasks: Vec<_> = patches_by_file
            .into_iter()
            .map(|(file_path, file_patches)| {
                let repo = repo.clone();
                let target_commit = target_commit.clone();

                tokio::spawn(async move {
                    self.apply_file_patches(&repo, file_patches, &target_commit).await
                })
            })
            .collect();

        // Wait for all tasks to complete
        let results = futures::future::try_join_all(tasks).await?;

        // Flatten results
        Ok(results.into_iter().flatten().collect())
    }
}
```
