# User Interface Design

Git Patchdance provides both terminal and graphical interfaces, each optimized for their respective environments while maintaining consistent functionality and user experience.

## Design Principles

- **Visual Clarity**: Clear visual hierarchy and intuitive layout
- **Keyboard Efficiency**: Vim-like keybindings for power users
- **Safety First**: Always preview changes before applying
- **Contextual Help**: Inline help and tooltips for complex operations
- **Responsive Design**: Efficient handling of large repositories

## Terminal User Interface (TUI)

### Layout Overview

```
┌─ Git Patchdance ─────────────────────────────────────────────────────────────────┐
├─ Repository: /path/to/repo ── Branch: main ── Status: Clean ────────────────────────┤
├──────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ Commit History ─────────┐ ┌─ Patch View ──────────────────────────────────────┐ │
│ │ * abc123 Fix bug in... │ │ @@ -15,7 +15,7 @@ fn calculate() {           │ │
│ │ * def456 Add feature   │ │ -    let result = old_function();                 │ │
│ │ * ghi789 Update docs   │ │ +    let result = new_function();                 │ │
│ │ * jkl012 Initial commit│ │                                                   │ │
│ │                        │ │ Files changed:                                    │ │
│ │ [5 commits total]      │ │ ■ src/main.rs                                     │ │
│ │                        │ │ ■ src/utils.rs                                    │ │
│ └────────────────────────┘ └───────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ Operations ──────────────────────────────────────────────────────────────────┐ │
│ │ [M]ove patch  [S]plit commit  [C]reate commit  [P]review  [U]ndo  [Q]uit     │ │
│ │                                                                              │ │
│ │ Ready: Select commits and patches to move                                    │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Panel Descriptions

#### Commit History Panel (Left)
- **Purpose**: Browse and select commits from repository history
- **Features**:
  - Scrollable commit list with graph visualization
  - Multi-select capability with visual indicators
  - Commit filtering (author, date, message)
  - Branch navigation and ref display

**Navigation:**
- `j/k` or `↑/↓`: Navigate commits
- `Space`: Select/deselect commit
- `Enter`: Focus on selected commit
- `/`: Search commits
- `b`: Switch branch

#### Patch View Panel (Right)
- **Purpose**: Display and select patches from focused commit
- **Features**:
  - Syntax-highlighted diff display
  - Individual file selection
  - Hunk-level patch selection
  - Conflict detection and resolution

**Navigation:**
- `j/k` or `↑/↓`: Navigate patches/hunks
- `Space`: Select/deselect patch
- `Enter`: Expand/collapse hunk
- `f`: Focus on file
- `h`: Toggle help

#### Operations Panel (Bottom)
- **Purpose**: Execute patch operations and display status
- **Features**:
  - Operation buttons with keyboard shortcuts
  - Progress indicators for long operations
  - Error messages and warnings
  - Undo/redo history

### Modal Dialogs

#### Move Patch Dialog
```
┌─ Move Patch ─────────────────────────────────┐
│                                              │
│ Move patch from: abc123 (Fix bug in...)      │
│ To target commit: [def456] Add feature       │
│                                              │
│ Patches to move:                             │
│ ☑ src/main.rs (lines 15-20)                 │
│ ☐ src/utils.rs (lines 5-10)                 │
│                                              │
│ [ Preview ] [ Move ] [ Cancel ]              │
└──────────────────────────────────────────────┘
```

#### Create Commit Dialog
```
┌─ Create New Commit ──────────────────────────┐
│                                              │
│ Commit message:                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Add error handling for network requests  │ │
│ │                                          │ │
│ │                                          │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Patches to include:                          │
│ ☑ src/network.rs (Error handling)           │
│ ☑ src/main.rs (Error display)               │
│                                              │
│ Position: [ After current ] [ At end ]      │
│                                              │
│ [ Create ] [ Cancel ]                        │
└──────────────────────────────────────────────┘
```

### Color Scheme

#### Default Theme
- **Background**: Dark blue (#1e2124)
- **Foreground**: Light gray (#dcddde)
- **Accent**: Orange (#faa61a)
- **Success**: Green (#43b581)
- **Warning**: Yellow (#faa61a)
- **Error**: Red (#f04747)
- **Selection**: Blue (#7289da)

#### Syntax Highlighting
- **Added lines**: Green background
- **Removed lines**: Red background
- **Context**: Default foreground
- **Line numbers**: Dimmed
- **Diff headers**: Bold cyan

## Graphical User Interface (GUI)

### Layout Overview

The GUI provides a more visual approach with drag-and-drop functionality and mouse interaction.

```
┌─ Git Patchdance ────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help                                          │
├─────────────────────────────────────────────────────────────────────────┤
│ 📁 /path/to/repo  🌿 main  ✅ Clean                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ┌─ Commit Timeline ───────────────────────────────────────────────────┐ │
│ │ ● abc123 ──── def456 ──── ghi789 ──── jkl012                       │ │
│ │   Fix bug     Add feat    Update      Initial                       │ │
│ │                                                                     │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─ Selected Commit: abc123 ─┐ ┌─ Target Operations ─────────────────┐ │
│ │                           │ │                                     │ │
│ │ Files changed:            │ │ 📋 Patches to move:                 │ │
│ │ ┌───────────────────────┐ │ │ • src/main.rs (lines 15-20)        │ │
│ │ │ 📄 src/main.rs       │ │ │ • src/utils.rs (lines 5-10)         │ │
│ │ │   + 5 lines          │ │ │                                     │ │
│ │ │   - 3 lines          │ │ │ 🎯 Target: def456                   │ │
│ │ │                      │ │ │                                     │ │
│ │ │ 📄 src/utils.rs      │ │ │ [Move Patches]  [Create Commit]     │ │
│ │ │   + 2 lines          │ │ │ [Preview]       [Cancel]            │ │
│ │ │   - 1 line           │ │ │                                     │ │
│ │ └───────────────────────┘ │ └─────────────────────────────────────┘ │
│ └───────────────────────────┘                                         │
│                                                                         │
│ ┌─ Diff Viewer ───────────────────────────────────────────────────────┐ │
│ │ @@ -15,7 +15,7 @@ fn calculate() {                                   │ │
│ │ - let result = old_function();                                     │ │
│ │ + let result = new_function();                                     │ │
│ │                                                                    │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### GUI Features

#### Interactive Timeline
- Visual commit graph with drag-and-drop
- Hover tooltips showing commit details
- Branch visualization with color coding
- Zoom and pan for large histories

#### Patch Selection
- Checkboxes for individual files and hunks
- Visual diff with line-by-line selection
- Drag patches between commits
- Preview window for operations

#### Modern UI Elements
- Native file dialogs
- Progress bars for operations
- Notification system
- Tabbed interface for multiple repositories

## Interaction Patterns

### Common Workflows

#### Moving a Patch
1. **TUI**: Select source commit → navigate to patch → press 'M' → select target → confirm
2. **GUI**: Click source commit → drag patch to target commit → confirm dialog

#### Splitting a Commit
1. **TUI**: Select commit → press 'S' → select patches to extract → choose operation
2. **GUI**: Right-click commit → "Split Commit" → checkbox patches → drag to new position

#### Creating New Commit
1. **TUI**: Select patches from multiple commits → press 'C' → enter message → confirm
2. **GUI**: Multi-select patches → "Create Commit" button → fill dialog → confirm

### Keyboard Shortcuts

#### Global Shortcuts
- `Ctrl+Q`: Quit application
- `Ctrl+Z`: Undo last operation  
- `Ctrl+Y`: Redo operation
- `F1`: Show help
- `F5`: Refresh repository

#### TUI Specific
- `Tab`: Switch between panels
- `Esc`: Cancel current operation
- `?`: Show contextual help
- `:`: Command mode
- `g`/`G`: Go to first/last commit

#### GUI Specific  
- `Ctrl+O`: Open repository
- `Ctrl+T`: New tab
- `Ctrl+W`: Close tab
- `Ctrl+F`: Find commits
- `F11`: Toggle fullscreen

## Accessibility

### TUI Accessibility
- High contrast color schemes
- Screen reader compatibility
- Keyboard-only navigation
- Customizable key bindings

### GUI Accessibility
- Scalable fonts and UI elements
- Alternative text for icons
- Keyboard navigation fallbacks
- Screen reader support

## Responsive Design

### Terminal Adaptation
- Automatic layout adjustment for terminal size
- Collapsible panels for narrow terminals
- Horizontal scrolling for wide content
- Graceful degradation for small screens

### Multi-Monitor Support
- Remember window positions
- Per-monitor DPI scaling
- Drag windows between monitors
- Context preservation across moves