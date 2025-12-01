# Document Structure Feature

This document describes the LaTeX-like document structure feature for the Book Writer application.

## Overview

The structure feature provides hierarchical document organization with:
- **Parts** → **Chapters** → **Sections** → **Subsections** → **Subsubsections** → **Paragraphs**
- Auto-numbering with configurable schemes
- Cross-references with labels
- Table of Contents (TOC)
- Virtual pagination
- Export to JSON, Markdown, Plain Text, and LaTeX
- **AI Outline Generation**: Generate structured outlines from freeform text
- **Outline Preview**: Review and approve AI-generated outlines before conversion
- **Document Preview**: Preview full document with approve button to send to writer
- **Full Persistence**: All data persists across navigation and page reloads

## Getting Started

### Enabling Structure Mode

Click the **"Structure"** button in the top toolbar to switch from simple editor to structure mode.

### Generating an Outline with AI

1. Write or paste your content in the simple writer mode
2. Click the **AI** button and select **"Outline"** mode
3. The outline preview page will open automatically
4. Review the generated outline structure
5. Click **"✓ Approve & Convert to Document"** to convert it to structured format
6. You'll be taken to the Structure page with your outline converted to nodes

### Navigating Between Modes

- **Structure → Writer Home**: Click **"← Writer Home"** button at the top of Structure page
- **Writer → Structure**: Click **"Structure"** button in the writer toolbar
- All data is automatically saved and restored when switching modes

### Creating Your First Document

1. Click **"Structure"** to enter structure mode
2. Use the toolbar buttons or keyboard shortcuts to create nodes:
   - **Part**: `Cmd/Ctrl+Alt+P`
   - **Chapter**: `Cmd/Ctrl+Alt+1`
   - **Section**: `Cmd/Ctrl+Alt+2`
   - **Subsection**: `Cmd/Ctrl+Alt+3`
   - **Subsubsection**: `Cmd/Ctrl+Alt+4`
   - **Paragraph**: `Cmd/Ctrl+Alt+Enter`

## User Interface

### Left Panel: Outline & Structure

The outline panel shows your document tree with:
- Icons for each node type
- Numbers (when numbered)
- Titles
- Word counts
- Drag-and-drop reordering
- Expand/collapse for nodes with children
- Search functionality

### Center: Editor

The main editor area includes:
- **Top Toolbar**: "← Writer Home" button for easy navigation back to simple mode
- **Node Toolbar**: Create, promote, demote, split, merge nodes
- **Breadcrumb**: Shows current location in hierarchy (e.g., "Part I › Chapter 2 › Section 2.3")
- **Editor**: 
  - **Title Editor**: Edit title for any node type (always visible)
  - **Content Editor**: Edit content for all node types (parts, chapters, sections, etc.)
  - All nodes are fully editable - no restrictions

### Right Panel: Properties (Optional)

Shows properties for the selected node:
- Title
- Label (for cross-references)
- Numbering toggle
- Node kind
- Metadata

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl+Alt+P` | New Part |
| `Cmd/Ctrl+Alt+1` | New Chapter |
| `Cmd/Ctrl+Alt+2` | New Section |
| `Cmd/Ctrl+Alt+3` | New Subsection |
| `Cmd/Ctrl+Alt+4` | New Subsubsection |
| `Cmd/Ctrl+Alt+Enter` | New Paragraph |
| `Shift+Tab` | Promote node |
| `Tab` | Demote node (at line start) |
| `Cmd/Ctrl+Up` | Jump to parent |
| `Alt+Down/Up` | Jump to next/prev sibling |
| `Cmd/Ctrl+R` | Insert reference |
| `Cmd/Ctrl+Shift+P` | Toggle page mode |

## Numbering Schemes

### Default Schemes

- **Parts**: Roman numerals (I, II, III, ...)
- **Chapters**: Arabic numerals (1, 2, 3, ...)
- **Sections**: Dotted notation (1.1, 1.2, ...)
- **Subsections**: Dotted notation (1.1.1, 1.1.2, ...)
- **Subsubsections**: Dotted notation (1.1.1.1, 1.1.1.2, ...)

### Customizing Numbering

1. Select a node in the outline
2. Open the Properties panel
3. Toggle "Numbered" to enable/disable numbering for that node
4. Numbering schemes can be configured per level in settings

## Cross-References

### Adding Labels

1. Select a node in the outline
2. Open the Properties panel
3. Enter a label in the "Label" field (e.g., `intro-section`)
4. Labels must be unique

### Inserting References

1. Place cursor where you want the reference
2. Press `Cmd/Ctrl+R` (or use the reference picker)
3. Select the target node
4. Reference will display as "Section 2.3" and update automatically when renumbered

### Reference Syntax

In content, you can use:
- `\ref{label}` - LaTeX style
- `[ref:label]` - Bracket style
- `{{ref:label}}` - Double bracket style

References are automatically resolved in exports.

## Table of Contents

### Viewing TOC

Click the **"TOC"** button in the bottom toolbar to view the table of contents.

The TOC shows:
- All numbered nodes
- Hierarchical structure
- Clickable navigation to sections

### TOC in Exports

- **Markdown**: TOC is rendered as heading links
- **LaTeX**: `\tableofcontents` is included if a TOC node exists
- **Plain Text**: TOC is shown as indented list

## Page Mode

### Enabling Page Mode

1. Click **"Page Mode"** in the bottom toolbar
2. Or press `Cmd/Ctrl+Shift+P`

### Features

- Virtual pagination based on configurable words-per-page (default: 300)
- Per-chapter page counts
- Page breaks can be pinned
- Word counts shown per page

## Document Preview

### Previewing Your Document

1. Click **"📄 Preview Document"** button in the bottom toolbar
2. A modal window opens showing your full document rendered with:
   - Proper heading sizes (Parts = 3xl, Chapters = 2xl, Sections = xl, etc.)
   - Auto-numbering displayed (e.g., "1", "1.1", "1.1.1")
   - All content formatted and readable
   - Hierarchical indentation

### Approving and Sending to Writer

1. Review your document in the preview
2. Click **"✓ Approve"** button in the preview header
3. The document is converted to plain text and sent to the writer home page
4. You can continue editing in simple writer mode

## Data Persistence

### Automatic Saving

- **Autosave**: Changes save automatically every 1 second
- **Before Navigation**: State is saved immediately when navigating away
- **Before Page Unload**: State is saved when closing the browser
- **Dual Storage**: Data is saved to both IndexedDB and localStorage for reliability

### State Restoration

When you return to Structure mode:
- Your draft ID is automatically restored
- All nodes and content are loaded from storage
- Your work continues exactly where you left off

### Draft Management

- **Writer Draft**: Stored in `writer_current_draft` (localStorage)
- **Structure Draft**: Stored in `writer_current_structure_draft` (localStorage)
- Both drafts are independent and persist across sessions

## Export Formats

### JSON (Lossless)

Exports the complete document structure including:
- All nodes with metadata
- Labels and references
- Settings
- Version history

**Use case**: Backup, migration, programmatic processing

### Markdown

Exports as Markdown with:
- Headings (`#`, `##`, etc.) for hierarchy
- Reference links `[Section 2.3](#sec-2-3)`
- Stable anchors based on labels or titles

**Use case**: Publishing to Markdown-based platforms, GitHub, documentation

### Plain Text

Exports as flattened text with:
- Numbered headings with indentation
- Inline references as text ("Section 2.3")
- Simple formatting

**Use case**: Simple text editors, email, basic formatting

### LaTeX

Exports as LaTeX document with:
- `\part`, `\chapter`, `\section`, etc. commands
- `\label{}` and `\ref{}` for references
- `\tableofcontents` if TOC exists
- Minimal preamble (no external packages)

**Use case**: Academic writing, typesetting, PDF generation

## Import

### JSON Import

1. Click **"Import"** in the bottom toolbar
2. Select a JSON file exported from the structure feature
3. Document structure is restored with all labels and references intact

## AI Integration

### Outline Generation

The structure feature includes AI-powered outline generation:

1. **Generate Outline**: 
   - Click AI button → Select "Outline" mode
   - AI analyzes your content and generates a structured outline
   - Outline preview page opens automatically

2. **Outline Preview Page**:
   - Review the generated outline structure
   - Expand/collapse chapters and sections
   - View statistics (chapters, sections, beats)
   - Edit the outline if needed (before approval)

3. **Approve & Convert**:
   - Click "✓ Approve & Convert to Document"
   - Outline is converted to structured document nodes
   - Automatically navigates to Structure page
   - All nodes are ready for editing

### Other AI Features

- **Insert Section Here**: Suggests section titles and starter paragraphs based on context
- **Retitle & Summarize**: Suggests concise titles and summaries for nodes
- **Cross-Reference Helper**: Suggests relevant nodes to cross-reference based on user intent

## Data Model

### Document Structure

```typescript
interface DocumentState {
  rootId: string;
  nodes: Record<string, DocNode>;
  settings: {
    numbering: NumberingSettings;
    pageMode: PageModeSettings;
  };
  labels: Record<string, string>; // label -> nodeId
  versions: Version[];
}

interface DocNode {
  id: string;
  kind: NodeKind;
  parentId: string | null;
  order: number;
  title?: string;
  content?: string;
  label?: string;
  numbered?: boolean;
  number?: string; // computed
  meta?: Record<string, any>;
}
```

### Valid Parent-Child Relationships

- `root` → `part`, `chapter`
- `part` → `chapter`
- `chapter` → `section`, `page`, `paragraph`
- `section` → `subsection`, `paragraph`
- `subsection` → `subsubsection`, `paragraph`
- `subsubsection` → `paragraph`
- `page` → `paragraph`

## Performance

The structure feature is optimized for large documents:
- Virtualized tree rendering (handles 500+ sections smoothly)
- Memoized numbering computation
- Efficient drag-and-drop
- Lazy loading of node content

## Accessibility

- Full keyboard navigation
- ARIA labels on all interactive elements
- Screen reader support
- High contrast mode support

## Troubleshooting

### Nodes not saving when exiting Structure page

- Check browser console for save/load messages
- Verify localStorage is enabled in your browser
- Check that `writer_current_structure_draft` exists in localStorage
- Try refreshing the page - data should persist

### Nodes not loading when returning to Structure page

- Check browser console for "Loading from storage" messages
- Verify the draft ID matches between sessions
- Check localStorage for `writer_structure_<draftId>` key
- Try clicking "Structure" button again to reload

### Numbers not updating

- Ensure nodes are numbered (check Properties panel)
- Verify numbering scheme is not set to "none" for that level
- Try promoting/demoting to trigger renumbering

### References not working

- Ensure target node has a label
- Check label is unique
- Verify reference syntax matches one of the supported formats

### Drag-and-drop not working

- Ensure you're dragging by the node icon/area
- Check that target parent allows the node kind as child
- Verify no cycles would be created

### Node selection not working

- Click directly on the node title or icon
- Avoid clicking on the expand/collapse button (it only toggles expansion)
- Wait for the click to register (drag requires 8px movement)
- Check browser console for "Selecting node" messages

### Outline preview not showing

- Ensure outline was generated successfully
- Check browser console for parsing errors
- Verify the outline JSON is valid
- Try generating the outline again

## Examples

### Creating a Book Structure

1. Click **"Structure"** button to enter structure mode
2. Create Part I: "Introduction" (use toolbar or `Cmd/Ctrl+Alt+P`)
3. Add Chapter 1: "Getting Started" (use toolbar or `Cmd/Ctrl+Alt+1`)
4. Add Section 1.1: "Installation" (use toolbar or `Cmd/Ctrl+Alt+2`)
5. Add Subsection 1.1.1: "System Requirements" (use toolbar or `Cmd/Ctrl+Alt+3`)
6. Click on each node to edit title and content
7. Add labels to key sections (in Properties panel)
8. Insert cross-references (use `Cmd/Ctrl+R` or reference picker)
9. Preview document (click "📄 Preview Document")
10. Export to LaTeX for typesetting (use Export dropdown)

### Converting Freeform to Structure with AI

1. Write content in simple editor mode
2. Click **AI** button → Select **"Outline"** mode
3. Outline preview page opens automatically
4. Review the generated outline structure
5. Expand/collapse to see all chapters and sections
6. Click **"✓ Approve & Convert to Document"**
7. You're taken to Structure page with outline converted to nodes
8. Edit nodes, add content, and continue writing

### Using Document Preview

1. Create and edit your structured document
2. Click **"📄 Preview Document"** in bottom toolbar
3. Review the full rendered document
4. Click **"✓ Approve"** to send to writer home page
5. Document appears in simple writer mode as plain text
6. Continue editing in simple mode or return to structure mode

## Technical Details

### Storage

Structured documents are stored with multiple persistence layers:

- **IndexedDB**: Primary storage for structured drafts and versions
- **localStorage**: Backup storage for reliability and quick access
- **Autosave**: Every 1 second (reduced from 10 seconds for better persistence)
- **Immediate Save**: Before navigation, page unload, and mode switching
- **Draft Tracking**: Current draft IDs stored in localStorage for restoration
- **Automatic Versioning**: Max 20 versions per draft

### Persistence Flow

1. **Editing**: Changes trigger autosave after 1 second
2. **Navigation**: State saved synchronously to localStorage before navigation
3. **Page Unload**: `beforeunload` handler saves state immediately
4. **Restoration**: On return, draft ID is loaded from localStorage, then state is restored

### Numbering Algorithm

Numbering is computed breadth-first:
1. Traverse tree level by level
2. For each numbered node, increment counter
3. Build number from counter chain
4. Format according to scheme (roman, arabic, dotted)

### Reference Resolution

References are resolved in two phases:
1. **Editor**: Show as clickable chips with target preview
2. **Export**: Resolve to human-readable text or links

## Workflow Examples

### Complete Workflow: From Idea to Structured Document

1. **Start Writing**: Write freeform text in simple writer mode
2. **Generate Outline**: Use AI "Outline" feature to create structure
3. **Review Outline**: Check outline preview page, expand sections
4. **Approve**: Convert outline to structured document
5. **Edit Structure**: Add/edit nodes, content, and organization
6. **Preview**: Use document preview to see final result
7. **Export**: Export to desired format (Markdown, LaTeX, etc.)
8. **Continue**: Switch between simple and structure modes as needed

### Editing Workflow

1. **Select Node**: Click any node in the outline panel
2. **Edit Title**: Change title in the top input field
3. **Edit Content**: Type content in the textarea below
4. **Auto-save**: Changes save automatically every 1 second
5. **Navigate Away**: Click "← Writer Home" - state is saved immediately
6. **Return**: Click "Structure" - all nodes are restored automatically

## Browser Compatibility

- **Chrome/Edge**: Full support (IndexedDB + localStorage)
- **Firefox**: Full support (IndexedDB + localStorage)
- **Safari**: Full support (IndexedDB + localStorage)
- **Mobile Browsers**: Supported with localStorage fallback

## Data Storage Details

### localStorage Keys

- `writer_current_draft`: Current writer draft ID
- `writer_current_structure_draft`: Current structure draft ID
- `writer_structure_<draftId>`: Structure document state (backup)
- `writer_draft_<draftId>`: Writer document state (backup)
- `pending_outline`: Temporary outline data (cleared after approval)

### IndexedDB Stores

- `structured_drafts`: Main storage for structured documents
- `structured_versions`: Version history (max 20 per draft)
- `drafts`: Simple writer drafts
- `versions`: Writer version history

## Future Enhancements

- Collaborative editing
- Version diff visualization
- Custom numbering schemes
- More export formats (PDF, EPUB)
- Advanced search and filtering
- Node templates
- Batch operations
- Real-time collaboration
- Cloud sync

## Support

For issues or questions:
- Check this documentation
- Review test files in `src/features/structure/__tests__/`
- Check browser console for error messages and debug logs
- Verify localStorage and IndexedDB are enabled in your browser

