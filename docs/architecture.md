# Architecture Overview

Git Patchdance is designed as a modular system with clear separation of concerns, enabling both terminal and graphical interfaces while maintaining a robust core for git operations.

## System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        TUI[Terminal UI<br/>ratatui]
        GUI[Graphical UI<br/>egui]
    end
    
    subgraph "Application Layer"
        APP[Application Core<br/>State Management]
        CMD[Command Handler<br/>Action Processing]
    end
    
    subgraph "Domain Layer"
        PM[Patch Manager<br/>Core Logic]
        GIT[Git Service<br/>Repository Operations]
        DIFF[Diff Engine<br/>Patch Analysis]
    end
    
    subgraph "Infrastructure Layer"
        REPO[Repository<br/>git2 bindings]
        FS[File System<br/>Temp files, Config]
        LOG[Logging<br/>tracing]
    end
    
    TUI --> APP
    GUI --> APP
    APP --> CMD
    CMD --> PM
    PM --> GIT
    PM --> DIFF
    GIT --> REPO
    DIFF --> REPO
    APP --> FS
    APP --> LOG
```

## Core Components

### User Interface Layer

#### Terminal UI (TUI)
- **Framework**: ratatui with crossterm backend
- **Layout**: Multi-pane interface with commit browser, patch viewer, and operation panel
- **Interaction**: Keyboard-driven navigation with vim-like keybindings
- **Features**: Syntax highlighting, scrollable views, modal dialogs

#### Graphical UI (GUI) 
- **Framework**: egui with native windowing
- **Layout**: Tabbed interface with drag-and-drop support
- **Interaction**: Mouse and keyboard input
- **Features**: Visual diff rendering, interactive patch selection

### Application Layer

#### Application Core
Central state management and coordination between UI and domain layers.

**Responsibilities:**
- Application state management (current repository, selected commits, etc.)
- UI state synchronization 
- Event routing and coordination
- Undo/redo history management

**Key Structures:**
```rust
pub struct AppState {
    repository: Option<Repository>,
    commit_history: Vec<CommitInfo>,
    selected_commits: HashSet<CommitId>,
    patch_operations: Vec<PatchOperation>,
    ui_state: UiState,
}
```

#### Command Handler
Processes user actions and orchestrates domain operations.

**Responsibilities:**
- Action validation and preprocessing
- Operation queuing and execution
- Error handling and user feedback
- Progress tracking for long operations

### Domain Layer

#### Patch Manager
Core business logic for patch manipulation and git history operations.

**Key Operations:**
- Extract patches from commits (full or partial)
- Apply patches to target commits
- Create new commits from patch collections  
- Validate and preview operations
- Handle merge conflicts

**Key Structures:**
```rust
pub struct PatchManager {
    git_service: GitService,
    diff_engine: DiffEngine,
    operation_history: Vec<Operation>,
}

pub enum PatchOperation {
    MovePatch { from: CommitId, to: CommitId, patch: PatchId },
    SplitCommit { commit: CommitId, patches: Vec<PatchId> },
    CreateCommit { patches: Vec<PatchId>, message: String },
}
```

#### Git Service  
High-level git repository operations and state management.

**Responsibilities:**
- Repository detection and validation
- Commit traversal and filtering
- Branch and ref management
- Safe git operations with rollback capability

#### Diff Engine
Patch analysis, manipulation, and conflict resolution.

**Responsibilities:**
- Parse and analyze git diffs
- Extract individual file changes
- Support partial patch selection
- Detect and resolve conflicts
- Generate preview diffs

### Infrastructure Layer

#### Repository Layer
Low-level git operations using git2 bindings.

**Responsibilities:**
- Direct git object manipulation
- Blob and tree operations
- Index management
- Reference updates

#### File System
Configuration and temporary file management.

**Responsibilities:**
- Application configuration
- Temporary patch files
- Operation state persistence
- Backup and recovery

## Data Flow

### Typical Operation Flow

1. **User Action**: User selects patches to move via UI
2. **Command Processing**: Action validated and queued
3. **Patch Extraction**: Source commits analyzed, patches extracted
4. **Preview Generation**: Changes previewed for user confirmation
5. **Operation Execution**: Git operations performed atomically
6. **State Update**: Application state refreshed, UI updated
7. **History Recording**: Operation recorded for undo capability

### Error Handling Strategy

- **Validation Layer**: Early validation of user inputs and git state
- **Atomic Operations**: All git changes performed as atomic transactions
- **Rollback Capability**: Automatic rollback on operation failure
- **User Feedback**: Clear error messages with suggested remediation
- **Recovery Mode**: Ability to recover from corrupted operation state

## Concurrency Model

- **Async Core**: All I/O operations are async using tokio
- **Background Tasks**: Long operations run in background with progress updates
- **UI Responsiveness**: UI remains responsive during git operations
- **Cancellation**: Support for cancelling long-running operations

## Security Considerations

- **Repository Validation**: Verify git repository integrity before operations
- **Path Sanitization**: Sanitize all file paths to prevent directory traversal
- **Operation Limits**: Prevent operations on extremely large repositories
- **Backup Strategy**: Automatic backups before destructive operations

## Performance Considerations

- **Lazy Loading**: Load commit history and diffs on demand
- **Caching Strategy**: Cache frequently accessed git objects
- **Memory Management**: Efficient handling of large repositories
- **Incremental Updates**: Update UI incrementally for large datasets