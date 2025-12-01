import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DocumentState, NodeKind } from './types';
import OutlinePanel from './OutlinePanel';
import NodeToolbar from './NodeToolbar';
import NodeProperties from './NodeProperties';
import Breadcrumb from './Breadcrumb';
import StructureEditor from './StructureEditor';
import TableOfContents from './TableOfContents';
import DocumentPreview from './DocumentPreview';
import { exportToMarkdown, exportToPlainText, exportToLaTeX, exportToJSON } from './exporters';
import { importFromJSON } from './importers/json';
import { useStructure } from './useStructure';
import { structureStorage } from './storage';
import { fileIO } from '../../lib/fileIO';

interface StructureViewProps {
  draftId: string;
  monospace?: boolean;
  focusMode?: boolean;
  initialState?: DocumentState;
}

export default function StructureView({
  draftId,
  monospace = false,
  initialState,
}: StructureViewProps) {
  const navigate = useNavigate();
  
  // Ensure draftId is set - try to get from localStorage first
  const savedDraftId = localStorage.getItem('writer_current_structure_draft');
  const effectiveDraftId = draftId || savedDraftId || `draft_${Date.now()}`;
  
  // Store the effective draftId in localStorage if it's new
  useEffect(() => {
    if (effectiveDraftId && effectiveDraftId !== savedDraftId) {
      localStorage.setItem('writer_current_structure_draft', effectiveDraftId);
    }
  }, [effectiveDraftId, savedDraftId]);
  
  console.log('StructureView rendering with:', {
    draftId: effectiveDraftId,
    hasInitialState: !!initialState,
    initialStateNodes: initialState ? Object.keys(initialState.nodes).length : 0,
    savedDraftId,
  });
  
  const {
    state,
    selectedNodeId,
    searchQuery,
    setState,
    setSelectedNodeId,
    setSearchQuery,
    createNode,
    moveNode,
    promoteNode,
  } = useStructure(effectiveDraftId, initialState);

  // Debug: Log selection changes
  useEffect(() => {
    console.log('Selected node changed:', selectedNodeId, selectedNodeId ? state.nodes[selectedNodeId]?.title : 'none');
  }, [selectedNodeId, state.nodes]);

  const [cursorPos, setCursorPos] = useState(0);
  const [showProperties] = useState(true);
  const [showTOC, setShowTOC] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [pageMode, setPageMode] = useState(state.settings.pageMode.enabled);

  // Debug: Log state changes
  useEffect(() => {
    console.log('StructureView state updated:', {
      totalNodes: Object.keys(state.nodes).length,
      chapters: Object.values(state.nodes).filter(n => n.kind === 'chapter').length,
      sections: Object.values(state.nodes).filter(n => n.kind === 'section').length,
      rootId: state.rootId,
      selectedNodeId,
    });
  }, [state, selectedNodeId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl+Alt+P for Part
      if ((e.ctrlKey || e.metaKey) && e.altKey && e.key === 'p') {
        e.preventDefault();
        const parentId = selectedNodeId && state.nodes[selectedNodeId] ? state.nodes[selectedNodeId].parentId : null;
        createNode(parentId, 'part');
      }
      // Cmd/Ctrl+Alt+1-5 for Chapter-Subsubsection
      else if ((e.ctrlKey || e.metaKey) && e.altKey && e.key >= '1' && e.key <= '5') {
        e.preventDefault();
        const kinds: NodeKind[] = ['chapter', 'section', 'subsection', 'subsubsection', 'paragraph'];
        const kind = kinds[parseInt(e.key) - 1];
        const parentId = selectedNodeId && state.nodes[selectedNodeId] ? state.nodes[selectedNodeId].parentId : null;
        createNode(parentId, kind);
      }
      // Cmd/Ctrl+Alt+Enter for Paragraph
      else if ((e.ctrlKey || e.metaKey) && e.altKey && e.key === 'Enter') {
        e.preventDefault();
        const parentId = selectedNodeId && state.nodes[selectedNodeId] ? state.nodes[selectedNodeId].parentId : null;
        createNode(parentId, 'paragraph');
      }
      // Shift+Tab for promote
      else if (e.shiftKey && e.key === 'Tab' && selectedNodeId) {
        e.preventDefault();
        promoteNode(selectedNodeId);
      }
      // Tab for demote (only at line start or when node selected)
      else if (e.key === 'Tab' && selectedNodeId && !e.ctrlKey && !e.metaKey) {
        // Let default tab behavior happen in textarea
      }
      // Cmd/Ctrl+R for insert reference
      else if ((e.ctrlKey || e.metaKey) && e.key === 'r' && selectedNodeId) {
        e.preventDefault();
        // Show reference picker - TODO: implement
        alert('Reference picker - coming soon');
      }
      // Cmd/Ctrl+Shift+P for page mode
      else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'p') {
        e.preventDefault();
        setPageMode(!pageMode);
        const newState = {
          ...state,
          settings: {
            ...state.settings,
            pageMode: {
              ...state.settings.pageMode,
              enabled: !pageMode,
            },
          },
        };
        setState(newState);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNodeId, state, createNode, promoteNode, pageMode, setState]);

  const handleExport = useCallback(async (format: 'json' | 'markdown' | 'plaintext' | 'latex') => {
    let content = '';
    let extension = '';
    let mimeType = 'text/plain';

    switch (format) {
      case 'json':
        content = exportToJSON(state);
        extension = 'json';
        mimeType = 'application/json';
        break;
      case 'markdown':
        content = exportToMarkdown(state);
        extension = 'md';
        mimeType = 'text/markdown';
        break;
      case 'plaintext':
        content = exportToPlainText(state);
        extension = 'txt';
        mimeType = 'text/plain';
        break;
      case 'latex':
        content = exportToLaTeX(state);
        extension = 'tex';
        mimeType = 'application/x-latex';
        break;
    }

    await fileIO.saveFile(`document.${extension}`, content, mimeType);
  }, [state]);

  const handleImport = useCallback(async () => {
    const file = await fileIO.openFile('.json');
    if (file && file.content) {
      try {
        const imported = importFromJSON(file.content);
        setState(imported);
        alert('Document imported successfully');
      } catch (error: any) {
        alert(`Import failed: ${error.message}`);
      }
    }
  }, [setState]);

  const handleNodeContentChange = useCallback((newState: DocumentState) => {
    setState(newState);
  }, [setState]);

  return (
    <div className="flex h-screen bg-white">
      {/* Left: Outline Panel */}
      <OutlinePanel
        state={state}
        selectedNodeId={selectedNodeId}
        onSelectNode={setSelectedNodeId}
        onMoveNode={moveNode}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Center: Editor */}
      <div className="flex-1 flex flex-col">
        {/* Top toolbar with home button */}
        <div className="border-b p-2 bg-gray-50 flex items-center justify-between">
          <button
            onClick={async () => {
              // Save state immediately and synchronously before navigating
              console.log('Saving structure state before navigation:', {
                draftId: effectiveDraftId,
                nodes: Object.keys(state.nodes).length,
                chapters: Object.values(state.nodes).filter(n => n.kind === 'chapter').length,
              });
              
              // Save to localStorage immediately (synchronous)
              try {
                localStorage.setItem(`writer_structure_${effectiveDraftId}`, JSON.stringify({ 
                  id: effectiveDraftId, 
                  state, 
                  updatedAt: Date.now() 
                }));
                // Store draftId for restoration
                localStorage.setItem('writer_current_structure_draft', effectiveDraftId);
                console.log('Structure state saved to localStorage:', effectiveDraftId);
              } catch (error) {
                console.error('Failed to save to localStorage:', error);
              }

              // Also try to save to IndexedDB (async, but don't wait)
              structureStorage.init().then(async () => {
                try {
                  await structureStorage.saveStructuredDraft(effectiveDraftId, state);
                  console.log('Structure state saved to IndexedDB:', effectiveDraftId);
                } catch (error) {
                  console.error('Failed to save to IndexedDB:', error);
                }
              }).catch(err => {
                console.error('Failed to init storage:', err);
              });

              // Navigate to writer home, clearing structure mode
              // Since we're using React Router with basename, navigate to "/" (root of basename)
              navigate('/', { 
                state: { structureMode: false },
                replace: false 
              });
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            title="Return to simple writer mode"
          >
            ← Writer Home
          </button>
          <div className="text-sm text-gray-600">
            Structure Mode
          </div>
        </div>
        
        {/* Toolbar */}
        <NodeToolbar
          state={state}
          selectedNodeId={selectedNodeId}
          caretPosition={cursorPos}
          onStateChange={setState}
        />

        {/* Breadcrumb */}
        <Breadcrumb
          state={state}
          nodeId={selectedNodeId}
          onNavigate={setSelectedNodeId}
        />

        {/* Editor */}
        <StructureEditor
          state={state}
          nodeId={selectedNodeId}
          onStateChange={handleNodeContentChange}
          onCursorChange={setCursorPos}
          onSelectionChange={() => {}}
          monospace={monospace}
        />

        {/* Bottom toolbar */}
        <div className="border-t p-2 bg-gray-50 flex items-center justify-between text-sm">
          <div className="flex gap-2">
            <button
              onClick={() => setShowTOC(!showTOC)}
              className="px-2 py-1 border rounded hover:bg-white"
            >
              TOC
            </button>
            <button
              onClick={() => setPageMode(!pageMode)}
              className="px-2 py-1 border rounded hover:bg-white"
            >
              Page Mode: {pageMode ? 'On' : 'Off'}
            </button>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowPreview(true)}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
              title="Preview full document"
            >
              📄 Preview Document
            </button>
            <button
              onClick={handleImport}
              className="px-2 py-1 border rounded hover:bg-white"
            >
              Import
            </button>
            <select
              onChange={(e) => {
                const format = e.target.value;
                if (format) {
                  handleExport(format as any);
                  e.target.value = ''; // Reset selection
                }
              }}
              className="px-2 py-1 border rounded"
              defaultValue=""
            >
              <option value="">Export...</option>
              <option value="json">JSON</option>
              <option value="markdown">Markdown</option>
              <option value="plaintext">Plain Text</option>
              <option value="latex">LaTeX</option>
            </select>
          </div>
        </div>
      </div>

      {/* Right: Properties Panel */}
      {showProperties && (
        <NodeProperties
          state={state}
          nodeId={selectedNodeId}
          onStateChange={setState}
        />
      )}

      {/* Document Preview Modal */}
      {showPreview && (
        <DocumentPreview
          state={state}
          onClose={() => setShowPreview(false)}
        />
      )}

      {/* TOC Modal */}
      {showTOC && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-lg w-96 h-96 overflow-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="font-semibold">Table of Contents</h2>
              <button
                onClick={() => setShowTOC(false)}
                className="px-2 py-1 hover:bg-gray-100 rounded"
              >
                ✕
              </button>
            </div>
            <TableOfContents
              state={state}
              onNavigate={(nodeId) => {
                setSelectedNodeId(nodeId);
                setShowTOC(false);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

