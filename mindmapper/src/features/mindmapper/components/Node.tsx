import { useState, useRef, useEffect } from 'react';
import { MindmapNode } from '../types';
import { calculateNodeSize } from '../utils/layout';

interface NodeProps {
  node: MindmapNode;
  selected: boolean;
  onSelect: () => void;
  onUpdate: (updates: Partial<MindmapNode>) => void;
  onDelete: () => void;
  viewX: number;
  viewY: number;
  zoom: number;
}

export default function Node({ node, selected, onSelect, onUpdate, viewX, viewY, zoom }: NodeProps) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(node.text);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing) {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.select();
      }
    }
  }, [editing]);

  const handleDoubleClick = () => {
    setEditing(true);
    setEditText(node.text);
  };

  const handleBlur = () => {
    setEditing(false);
    if (editText !== node.text) {
      const size = calculateNodeSize(editText);
      onUpdate({ text: editText, width: size.width, height: size.height });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleBlur();
    } else if (e.key === 'Escape') {
      setEditText(node.text);
      setEditing(false);
    }
  };

  const width = node.width || 100;
  const height = node.height || 40;
  const screenX = (node.x + viewX) * zoom;
  const screenY = (node.y + viewY) * zoom;
  const screenWidth = width * zoom;
  const screenHeight = height * zoom;

  const style: React.CSSProperties = {
    position: 'absolute',
    left: screenX - screenWidth / 2,
    top: screenY - screenHeight / 2,
    width: screenWidth,
    height: screenHeight,
    backgroundColor: node.color,
    color: node.textColor,
    border: selected ? '3px solid #4facfe' : '2px solid rgba(0,0,0,0.1)',
    borderRadius: node.shape === 'pill' ? screenHeight / 2 : '8px',
    padding: '8px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: `${14 * zoom}px`,
    boxShadow: selected ? '0 4px 12px rgba(79, 172, 254, 0.4)' : '0 2px 4px rgba(0,0,0,0.1)',
    userSelect: 'none',
    wordWrap: 'break-word',
    overflow: 'hidden',
    textAlign: 'center',
  };

  return (
    <div
      style={style}
      onClick={onSelect}
      onDoubleClick={handleDoubleClick}
    >
      {editing ? (
        <textarea
          ref={textareaRef}
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            outline: 'none',
            background: 'transparent',
            color: node.textColor,
            resize: 'none',
            textAlign: 'center',
            fontSize: `${14 * zoom}px`,
            fontFamily: 'inherit',
          }}
        />
      ) : (
        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {node.text || 'Empty'}
        </div>
      )}
    </div>
  );
}

