import { useState, useEffect } from 'react';
import { Mindmap } from '../types';

interface ToolbarProps {
  mindmap: Mindmap | null;
  onNew: () => void;
  onDuplicate: () => void;
  onExportJSON: () => void;
  onExportSVG: () => void;
  onExportPNG: () => void;
  onTitleChange: (title: string) => void;
  saving: boolean;
}

export default function Toolbar({
  mindmap,
  onNew,
  onDuplicate,
  onExportJSON,
  onExportSVG,
  onExportPNG,
  onTitleChange,
  saving,
}: ToolbarProps) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState(mindmap?.title || '');

  useEffect(() => {
    if (mindmap) {
      setTitleValue(mindmap.title);
    }
  }, [mindmap]);

  const handleTitleBlur = () => {
    setEditingTitle(false);
    if (titleValue && mindmap) {
      onTitleChange(titleValue);
    }
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleTitleBlur();
    } else if (e.key === 'Escape') {
      setTitleValue(mindmap?.title || '');
      setEditingTitle(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: '#fff',
        borderBottom: '1px solid #e0e0e0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      }}
    >
      <button
        onClick={onNew}
        style={{
          padding: '8px 16px',
          backgroundColor: '#4facfe',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500',
        }}
      >
        New Map
      </button>

      {mindmap && (
        <>
          <button
            onClick={onDuplicate}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Duplicate
          </button>

          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
            {editingTitle ? (
              <input
                type="text"
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
                onBlur={handleTitleBlur}
                onKeyDown={handleTitleKeyDown}
                style={{
                  flex: 1,
                  padding: '6px 12px',
                  border: '2px solid #4facfe',
                  borderRadius: '4px',
                  fontSize: '16px',
                  fontWeight: '500',
                  outline: 'none',
                }}
                autoFocus
              />
            ) : (
              <h2
                onClick={() => setEditingTitle(true)}
                style={{
                  flex: 1,
                  margin: 0,
                  fontSize: '18px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '4px',
                }}
                onMouseEnter={(e) => {
                  (e.target as HTMLElement).style.backgroundColor = '#f0f0f0';
                }}
                onMouseLeave={(e) => {
                  (e.target as HTMLElement).style.backgroundColor = 'transparent';
                }}
              >
                {mindmap.title}
              </h2>
            )}
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <div
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                color: saving ? '#ff9800' : '#4caf50',
                fontWeight: '500',
              }}
            >
              {saving ? 'Saving...' : 'All changes saved'}
            </div>

            <div style={{ width: '1px', height: '24px', backgroundColor: '#e0e0e0' }} />

            <button
              onClick={onExportJSON}
              style={{
                padding: '8px 16px',
                backgroundColor: '#fff',
                color: '#333',
                border: '1px solid #ddd',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Export JSON
            </button>

            <button
              onClick={onExportSVG}
              style={{
                padding: '8px 16px',
                backgroundColor: '#fff',
                color: '#333',
                border: '1px solid #ddd',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Export SVG
            </button>

            <button
              onClick={onExportPNG}
              style={{
                padding: '8px 16px',
                backgroundColor: '#fff',
                color: '#333',
                border: '1px solid #ddd',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Export PNG
            </button>
          </div>
        </>
      )}
    </div>
  );
}

