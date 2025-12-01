import { DocumentState, NodeKind } from './types';
import { createNode, promoteNode, demoteNode, splitAtCaret, mergeWithPrev } from './tree';

interface NodeToolbarProps {
  state: DocumentState;
  selectedNodeId: string | null;
  caretPosition?: number;
  onStateChange: (state: DocumentState) => void;
}

export default function NodeToolbar({
  state,
  selectedNodeId,
  caretPosition,
  onStateChange,
}: NodeToolbarProps) {
  const selectedNode = selectedNodeId ? state.nodes[selectedNodeId] : null;

  const handleCreate = (kind: NodeKind) => {
    const parentId = selectedNode?.parentId || null;
    const { state: newState } = createNode(state, parentId, kind);
    onStateChange(newState);
  };

  const handlePromote = () => {
    if (!selectedNodeId) return;
    try {
      const newState = promoteNode(state, selectedNodeId);
      onStateChange(newState);
    } catch (error: any) {
      alert(error.message);
    }
  };

  const handleDemote = () => {
    if (!selectedNodeId) return;
    try {
      const newState = demoteNode(state, selectedNodeId);
      onStateChange(newState);
    } catch (error: any) {
      alert(error.message);
    }
  };

  const handleSplit = () => {
    if (!selectedNodeId || caretPosition === undefined) return;
    try {
      const { state: newState } = splitAtCaret(state, selectedNodeId, caretPosition);
      onStateChange(newState);
    } catch (error: any) {
      alert(error.message);
    }
  };

  const handleMerge = () => {
    if (!selectedNodeId) return;
    try {
      const newState = mergeWithPrev(state, selectedNodeId);
      onStateChange(newState);
    } catch (error: any) {
      alert(error.message);
    }
  };

  return (
    <div className="flex gap-1 p-2 border-b bg-gray-50 flex-wrap">
      <button
        onClick={() => handleCreate('part')}
        className="px-2 py-1 text-xs border rounded hover:bg-white"
        title="New Part (Cmd/Ctrl+Alt+P)"
      >
        Part
      </button>
      <button
        onClick={() => handleCreate('chapter')}
        className="px-2 py-1 text-xs border rounded hover:bg-white"
        title="New Chapter (Cmd/Ctrl+Alt+1)"
      >
        Chapter
      </button>
      <button
        onClick={() => handleCreate('section')}
        className="px-2 py-1 text-xs border rounded hover:bg-white"
        title="New Section (Cmd/Ctrl+Alt+2)"
      >
        Section
      </button>
      <button
        onClick={() => handleCreate('subsection')}
        className="px-2 py-1 text-xs border rounded hover:bg-white"
        title="New Subsection (Cmd/Ctrl+Alt+3)"
      >
        Subsection
      </button>
      <button
        onClick={() => handleCreate('paragraph')}
        className="px-2 py-1 text-xs border rounded hover:bg-white"
        title="New Paragraph (Cmd/Ctrl+Alt+Enter)"
      >
        Paragraph
      </button>
      
      <div className="w-px bg-gray-300 mx-1" />
      
      <button
        onClick={handlePromote}
        disabled={!selectedNodeId}
        className="px-2 py-1 text-xs border rounded hover:bg-white disabled:opacity-50"
        title="Promote (Shift+Tab)"
      >
        ↑
      </button>
      <button
        onClick={handleDemote}
        disabled={!selectedNodeId}
        className="px-2 py-1 text-xs border rounded hover:bg-white disabled:opacity-50"
        title="Demote (Tab)"
      >
        ↓
      </button>
      
      <div className="w-px bg-gray-300 mx-1" />
      
      <button
        onClick={handleSplit}
        disabled={!selectedNodeId || caretPosition === undefined}
        className="px-2 py-1 text-xs border rounded hover:bg-white disabled:opacity-50"
        title="Split at cursor"
      >
        Split
      </button>
      <button
        onClick={handleMerge}
        disabled={!selectedNodeId}
        className="px-2 py-1 text-xs border rounded hover:bg-white disabled:opacity-50"
        title="Merge with previous"
      >
        Merge
      </button>
    </div>
  );
}

