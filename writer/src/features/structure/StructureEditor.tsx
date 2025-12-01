import { useEffect, useRef } from 'react';
import { DocumentState } from './types';

interface StructureEditorProps {
  state: DocumentState;
  nodeId: string | null;
  onStateChange: (state: DocumentState) => void;
  onCursorChange: (pos: number) => void;
  onSelectionChange: (selection: string) => void;
  onInsertReference?: (targetNodeId: string) => void;
  monospace?: boolean;
}

export default function StructureEditor({
  state,
  nodeId,
  onStateChange,
  onCursorChange,
  onSelectionChange,
  monospace = false,
}: StructureEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const node = nodeId ? state.nodes[nodeId] : null;

  // Scroll to node when selected
  useEffect(() => {
    if (nodeId && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [nodeId]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (!nodeId) return;

    const newContent = e.target.value;
    const node = state.nodes[nodeId];
    if (!node) return;

    const newNodes = { ...state.nodes };
    newNodes[nodeId] = {
      ...node,
      content: newContent,
    };

    onStateChange({ ...state, nodes: newNodes });

    const pos = e.target.selectionStart;
    onCursorChange(pos);

    const selection = e.target.value.slice(
      e.target.selectionStart,
      e.target.selectionEnd
    );
    onSelectionChange(selection);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Tab for demote, Shift+Tab for promote
    if (e.key === 'Tab' && !e.shiftKey) {
      // Let default tab behavior happen in textarea
      return;
    }

    if (e.key === 'Tab' && e.shiftKey) {
      // Promote - handled by parent via keyboard shortcuts
      return;
    }

    // Cmd/Ctrl+R for insert reference
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault();
      // Show reference picker - handled by parent
    }
  };

  if (!node) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <p>Select a node to edit</p>
      </div>
    );
  }

  const content = node.content || '';
  const title = node.title || '';

  // Handle title changes
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!nodeId) return;

    const newTitle = e.target.value;
    const node = state.nodes[nodeId];
    if (!node) return;

    const newNodes = { ...state.nodes };
    newNodes[nodeId] = {
      ...node,
      title: newTitle,
    };

    onStateChange({ ...state, nodes: newNodes });
  };

  return (
    <div className="flex-1 relative overflow-auto bg-white flex flex-col">
      {/* Title editor for all node types */}
      <div className="border-b p-4 bg-gray-50">
        <label className="block text-xs font-medium text-gray-700 mb-1">
          {node.kind.charAt(0).toUpperCase() + node.kind.slice(1)} Title
        </label>
        <input
          type="text"
          value={title}
          onChange={handleTitleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg font-semibold"
          placeholder={`Enter ${node.kind} title...`}
        />
      </div>

      {/* Content editor - show for ALL node types */}
      <textarea
        ref={textareaRef}
        value={content}
        onChange={handleContentChange}
        onKeyDown={handleKeyDown}
        className={`flex-1 w-full p-6 outline-none resize-none ${
          monospace ? 'font-mono' : ''
        }`}
        style={{
          fontSize: '16px',
          lineHeight: '1.6',
        }}
        placeholder={`Start writing ${node.kind} content...`}
        aria-label={`${node.kind} content editor`}
      />
    </div>
  );
}

