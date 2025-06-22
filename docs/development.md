# Development Guide

This guide covers setting up the development environment, building the project, testing, and contributing to Git Patchdance.

## Prerequisites

### Required Tools

- **Rust**: Version 1.70+ (install via [rustup](https://rustup.rs/))
- **Git**: Version 2.30+ for full feature compatibility  
- **Python**: Version 3.8+ (for documentation)
- **pkg-config**: For native dependencies
- **libgit2**: System library (optional, will build from source if not found)

### Platform-Specific Setup

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install build-essential pkg-config libgit2-dev libssl-dev
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install gcc pkg-config libgit2-devel openssl-devel
```

#### macOS
```bash
brew install pkg-config libgit2 openssl
```

#### Windows
```powershell
# Using vcpkg
vcpkg install libgit2:x64-windows openssl:x64-windows
```

## Project Setup

### Clone and Build

```bash
git clone https://github.com/RonnyPfannschmidt/git-patchdance.git
cd git-patchdance

# Build debug version
cargo build

# Build release version
cargo build --release

# Build with GUI support
cargo build --features gui

# Run the application
cargo run

# Run with GUI
cargo run --features gui -- --gui
```

### Development Environment

#### VS Code Setup

Recommended VS Code extensions:
```json
{
    "recommendations": [
        "rust-lang.rust-analyzer",
        "tamasfe.even-better-toml",
        "vadimcn.vscode-lldb",
        "serayuzgur.crates"
    ]
}
```

VS Code settings (`.vscode/settings.json`):
```json
{
    "rust-analyzer.cargo.features": ["tui"],
    "rust-analyzer.checkOnSave.command": "clippy",
    "rust-analyzer.checkOnSave.extraArgs": ["--", "-W", "clippy::all"]
}
```

#### Rust Analyzer Configuration

Create `.vscode/settings.json`:
```json
{
    "rust-analyzer.cargo.features": "all",
    "rust-analyzer.procMacro.enable": true,
    "rust-analyzer.cargo.loadOutDirsFromCheck": true
}
```

## Documentation

### Building Documentation

#### Code Documentation
```bash
# Build API documentation
cargo doc --open

# Build with all features
cargo doc --features gui --open

# Generate private items documentation  
cargo doc --document-private-items --open
```

#### User Documentation
```bash
# Install MkDocs and dependencies
pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Documentation Standards

- All public APIs must have documentation comments
- Use examples in documentation where appropriate
- Keep documentation up-to-date with code changes
- Use `///` for public item documentation
- Use `//!` for module-level documentation

Example:
```rust
/// Extracts patches from a git commit.
///
/// This function analyzes the diff between a commit and its parent(s)
/// to extract individual patches that can be manipulated independently.
///
/// # Arguments
///
/// * `commit_id` - The git commit ID to extract patches from
/// * `filter` - Optional filter to select specific files or hunks
///
/// # Returns
///
/// A vector of `Patch` objects representing the changes in the commit.
///
/// # Examples
///
/// ```rust
/// use git_patchdance::{PatchExtractor, CommitId};
///
/// let extractor = PatchExtractor::new(repo);
/// let patches = extractor.extract_patches(commit_id, None).await?;
/// println!("Found {} patches", patches.len());
/// ```
///
/// # Errors
///
/// Returns an error if:
/// - The commit ID is invalid
/// - The repository is in an inconsistent state
/// - Git operations fail
pub async fn extract_patches(
    &self,
    commit_id: CommitId,
    filter: Option<PatchFilter>,
) -> Result<Vec<Patch>> {
    // Implementation...
}
```

## Testing

### Running Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_patch_extraction

# Run tests for specific module
cargo test git_service

# Run integration tests only
cargo test --test integration

# Run with all features
cargo test --features gui
```

### Test Organization

```
tests/
├── integration/           # Integration tests
│   ├── git_operations.rs
│   ├── patch_management.rs
│   └── ui_workflows.rs
├── fixtures/              # Test data
│   ├── repos/
│   └── patches/
└── common/                # Test utilities
    ├── mod.rs
    └── test_repo.rs

src/
└── lib.rs
    ├── git_service/
    │   ├── mod.rs
    │   └── tests.rs       # Unit tests
    └── patch_manager/
        ├── mod.rs
        └── tests.rs       # Unit tests
```

### Writing Tests

#### Unit Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    
    #[tokio::test]
    async fn test_patch_extraction() {
        // Setup
        let temp_dir = TempDir::new().unwrap();
        let repo = create_test_repo(&temp_dir).await;
        let extractor = PatchExtractor::new(repo);
        
        // Execute
        let patches = extractor.extract_patches(commit_id, None).await.unwrap();
        
        // Verify
        assert_eq!(patches.len(), 2);
        assert_eq!(patches[0].target_file, PathBuf::from("src/main.rs"));
    }
    
    async fn create_test_repo(temp_dir: &TempDir) -> Repository {
        // Helper function to create test repository
        // Implementation...
    }
}
```

#### Integration Tests
```rust
use git_patchdance::{GitService, PatchManager, Repository};
use std::process::Command;
use tempfile::TempDir;

#[tokio::test]
async fn test_full_patch_workflow() {
    // Create test repository with history
    let test_repo = TestRepository::with_commits(&[
        ("Initial commit", &[("file1.txt", "content1")]),
        ("Add feature", &[("file2.txt", "content2")]),
        ("Fix bug", &[("file1.txt", "fixed content1")]),
    ]).await;
    
    // Initialize services
    let git_service = GitService::new();
    let patch_manager = PatchManager::new(git_service);
    
    // Extract patch from second commit
    let patches = patch_manager
        .extract_patches(&test_repo.repo, &test_repo.commits[1])
        .await
        .unwrap();
    
    // Move patch to third commit
    let result = patch_manager
        .move_patch(&patches[0], &test_repo.commits[2])
        .await
        .unwrap();
    
    // Verify result
    assert!(result.success);
    assert_eq!(result.conflicts.len(), 0);
}
```

### Test Utilities

Create common test utilities in `tests/common/mod.rs`:

```rust
use git2::{Repository as Git2Repository, Signature};
use std::fs;
use std::path::Path;
use tempfile::TempDir;

pub struct TestRepository {
    pub temp_dir: TempDir,
    pub repo: Git2Repository,
    pub commits: Vec<git2::Oid>,
}

impl TestRepository {
    pub async fn new() -> Self {
        let temp_dir = TempDir::new().unwrap();
        let repo = Git2Repository::init(temp_dir.path()).unwrap();
        
        // Set up test user
        let mut config = repo.config().unwrap();
        config.set_str("user.name", "Test User").unwrap();
        config.set_str("user.email", "test@example.com").unwrap();
        
        Self {
            temp_dir,
            repo,
            commits: Vec::new(),
        }
    }
    
    pub async fn with_commits(commits: &[(&str, &[(&str, &str)])]) -> Self {
        let mut test_repo = Self::new().await;
        
        for (message, files) in commits {
            test_repo.create_commit(message, files);
        }
        
        test_repo
    }
    
    pub fn create_commit(&mut self, message: &str, files: &[(&str, &str)]) -> git2::Oid {
        // Write files
        for (file_path, content) in files {
            let full_path = self.temp_dir.path().join(file_path);
            if let Some(parent) = full_path.parent() {
                fs::create_dir_all(parent).unwrap();
            }
            fs::write(&full_path, content).unwrap();
        }
        
        // Stage files
        let mut index = self.repo.index().unwrap();
        for (file_path, _) in files {
            index.add_path(Path::new(file_path)).unwrap();
        }
        index.write().unwrap();
        
        // Create commit
        let tree_id = index.write_tree().unwrap();
        let tree = self.repo.find_tree(tree_id).unwrap();
        let signature = Signature::now("Test User", "test@example.com").unwrap();
        
        let parents: Vec<_> = if self.commits.is_empty() {
            Vec::new()
        } else {
            vec![self.repo.find_commit(self.commits.last().unwrap().clone()).unwrap()]
        };
        
        let parent_refs: Vec<&git2::Commit> = parents.iter().collect();
        
        let commit_id = self.repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parent_refs,
        ).unwrap();
        
        self.commits.push(commit_id);
        commit_id
    }
}
```

## Code Quality

### Linting and Formatting

```bash
# Format code
cargo fmt

# Check formatting without making changes
cargo fmt -- --check

# Run clippy (linter)
cargo clippy

# Run clippy with all features
cargo clippy --features gui

# Run clippy with strict settings
cargo clippy -- -W clippy::all -W clippy::pedantic
```

### Pre-commit Hooks

Install pre-commit hooks using [pre-commit](https://pre-commit.com/):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --
        language: system
        types: [rust]
        
      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy --features gui -- -D warnings
        language: system
        types: [rust]
        pass_filenames: false
        
      - id: cargo-test
        name: cargo test
        entry: cargo test --features gui
        language: system
        types: [rust]
        pass_filenames: false
```

### Code Coverage

Generate code coverage reports:

```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Generate coverage report
cargo tarpaulin --features gui --out Html

# Generate coverage for CI
cargo tarpaulin --features gui --out Xml
```

## Benchmarking

### Performance Testing

```bash
# Install criterion
cargo install cargo-criterion

# Run benchmarks
cargo bench

# Run specific benchmark
cargo bench patch_extraction

# Generate benchmark reports
cargo criterion --message-format=json > benchmark_results.json
```

### Benchmark Structure

```rust
// benches/patch_operations.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use git_patchdance::{PatchExtractor, TestRepository};

fn bench_patch_extraction(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let test_repo = rt.block_on(TestRepository::with_large_history());
    let extractor = PatchExtractor::new(test_repo.repo.clone());
    
    c.bench_function("extract_patches_large_commit", |b| {
        b.to_async(&rt).iter(|| async {
            let patches = extractor
                .extract_patches(black_box(test_repo.commits[100]), None)
                .await
                .unwrap();
            black_box(patches);
        })
    });
}

criterion_group!(benches, bench_patch_extraction);
criterion_main!(benches);
```

## Contributing

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality
3. **Ensure all tests pass** and code is formatted
4. **Update documentation** for any API changes
5. **Submit a pull request** with clear description

### Commit Message Format

Follow conventional commits:

```
type(scope): description

Body explaining what and why vs. how

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix  
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(patch): add support for binary file patches

Implement binary patch detection and handling using git's
binary diff format. This enables moving binary files
between commits.

Fixes #45

test(git): add integration tests for merge conflicts

Add comprehensive test coverage for three-way merge
conflict detection and resolution workflows.

docs(api): update patch manager documentation

Clarify the behavior of patch application when conflicts
are detected and add examples for common use cases.
```

### Code Review Guidelines

#### For Contributors
- Keep PRs focused and reasonably sized
- Include tests for new functionality
- Update documentation
- Respond promptly to review feedback

#### For Reviewers
- Focus on correctness, performance, and maintainability
- Provide constructive feedback
- Test the changes locally when possible
- Check for proper error handling

## Release Process

### Version Management

Git Patchdance follows semantic versioning (SemVer):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Release Checklist

1. **Update version** in `Cargo.toml`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite** with all features
4. **Build release binaries** for all platforms
5. **Create git tag** and push to repository
6. **Publish to crates.io** (if applicable)
7. **Update documentation** and deploy

### Automated Releases

The project uses GitHub Actions for automated releases:

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']
    
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build release
        run: cargo build --release --features gui
      - name: Create release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
```